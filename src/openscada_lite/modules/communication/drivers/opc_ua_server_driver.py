# -----------------------------------------------------------------------------
# Copyright 2025 Daniel&Hector Fernandez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
import re
import uuid
from asyncua import Server, ua
from asyncua.common.subscription import Subscription
from openscada_lite.modules.communication.drivers.server_protocol import ServerProtocol
from openscada_lite.common.models.dtos import (
    DriverConnectStatus,
    TagUpdateMsg,
    SendCommandMsg,
)

import logging

logger = logging.getLogger(__name__)


class OPCUAServerDriver(ServerProtocol):
    """
    Async OPC UA Server driver with reconnect support:
      • Creates a fresh server instance every connect().
      • Uses stable string NodeIds to avoid collisions.
      • Single initialization method (_init_server()).
    """

    def __init__(self, server_name="OPCUAServer", **kwargs):
        self._server_name = server_name

        # Dynamic data updated per connection
        self.server: Server | None = None
        self.namespace_index: int | None = None
        self.namespace_url: str | None = None
        self.nodes: dict[str, ua.NodeId] = {}  # dp -> node
        self._nodes_cache: dict[str, str] = {}  # dp -> last value
        self.allow_write_regex = None
        self.endpoint = "opc.tcp://0.0.0.0:4840/freeopcua/server/"
        self.subscription: Subscription | None = None

        # External listeners
        self._command_listener = None
        self._communication_status_callback = None

        self._is_connected = False

    # ----------------------------------------------------------------------
    # Configuration
    # ----------------------------------------------------------------------
    def initialize(self, config: dict) -> None:
        self.namespace_url = config.get("namespaceurl", "http://default.namespace")  # NOSONAR
        self.allow_write_regex = re.compile(config.get("allow_write_regex", ".*_CMD$"))
        self.endpoint = config.get("endpoint", self.endpoint)

    def subscribe(self, datapoints: list) -> None:
        for dp in datapoints:
            self._nodes_cache[dp.name] = ""
        logger.info(f"[OPCUA] Will expose {len(self._nodes_cache)} nodes on connect()")

    def set_command_listener(self, listener):
        self._command_listener = listener

    def register_communication_status_listener(self, callback):
        self._communication_status_callback = callback

    # ----------------------------------------------------------------------
    # Unified server initialization (called only inside connect)
    # ----------------------------------------------------------------------
    async def _init_server(self):
        """
        Fully resets the server, rebuilds namespace, nodes, and subs.
        This is called ONLY from connect(), ensuring a fresh server every time.
        """
        # Fresh server instance avoids NodeId collisions
        self.server = Server()
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name(self._server_name)

        await self.server.init()
        self.namespace_index = await self.server.register_namespace(self.namespace_url)

        # Create nodes
        await self._create_nodes()

        # Start server
        await self.server.start()

        # Subscribe for writes
        self.subscription = await self.server.create_subscription(100, self)
        await self._setup_write_monitors()

    # ----------------------------------------------------------------------
    # Connect / Disconnect
    # ----------------------------------------------------------------------
    async def connect(self) -> None:
        """Start OPC UA server with a fresh instance."""
        await self._init_server()

        self._is_connected = True

        if self._communication_status_callback:
            await self.publish_driver_state("online")

        logger.info(
            f"[OPCUA] Server started at {self.endpoint} "
            f"(namespace: {self.namespace_url}, idx: {self.namespace_index})"
        )

    async def disconnect(self) -> None:
        """Shutdown server cleanly."""
        if self.subscription:
            try:
                await self.subscription.delete()
            except Exception as e:
                logger.warning(f"Error deleting subscription: {e}")

            self.subscription = None

        if self.server:
            try:
                await self.server.stop()
            except Exception as e:
                logger.warning(f"Error stopping server: {e}")

        self.server = None
        self.nodes.clear()

        self._is_connected = False

        if self._communication_status_callback:
            await self.publish_driver_state("offline")

        logger.info("[OPCUA] Server stopped")

    # ----------------------------------------------------------------------
    # Node creation
    # ----------------------------------------------------------------------
    async def _create_nodes(self):
        """Create variables with stable string NodeIds (no auto-numeric IDs)."""
        objects = self.server.get_objects_node()
        count = 0

        for dp_name, initial_value in self._nodes_cache.items():
            writable = bool(self.allow_write_regex.match(dp_name))

            # Stable ID (avoids collisions)
            nodeid = ua.NodeId(dp_name, self.namespace_index)

            node = await objects.add_variable(
                nodeid,
                dp_name,
                ua.Variant(initial_value, ua.VariantType.String),
            )

            if writable:
                await node.set_writable()
                await node.write_attribute(
                    ua.AttributeIds.UserWriteMask, ua.DataValue(ua.UInt32(1))
                )
                await node.write_attribute(ua.AttributeIds.WriteMask, ua.DataValue(ua.UInt32(1)))

            self.nodes[dp_name] = node
            count += 1

        logger.info(f"[OPCUA] Created {count} nodes")

    # ----------------------------------------------------------------------
    # Write monitoring
    # ----------------------------------------------------------------------
    async def _setup_write_monitors(self):
        """Subscribe data-change events only for writable nodes."""
        if not self.subscription:
            logger.warning("Subscription missing during write monitor setup")
            return

        watch_count = 0
        for dp_name, node in self.nodes.items():
            if self.allow_write_regex.match(dp_name):
                await self.subscription.subscribe_data_change(node)
                watch_count += 1

        logger.info(f"[OPCUA] Write monitoring enabled on {watch_count} nodes")

    async def datachange_notification(self, node, val, data):
        """Called when OPC UA client writes to a node."""
        dp_name = next((n for n, nd in self.nodes.items() if nd.nodeid == node.nodeid), None)
        if not dp_name:
            return

        val_str = str(val)
        logger.info(f"[WRITE] Client wrote {dp_name} -> '{val_str}'")

        if self._command_listener:
            msg = SendCommandMsg(
                datapoint_identifier=dp_name,
                value=val_str,
                command_id=str(uuid.uuid4()),
            )
            await self._command_listener.on_driver_command(msg)

    # ----------------------------------------------------------------------
    # Internal updates
    # ----------------------------------------------------------------------
    async def handle_tag_update(self, msg: TagUpdateMsg) -> None:
        """Update server node value from internal system."""
        dp_name = msg.datapoint_identifier
        val_str = str(msg.value)

        self._nodes_cache[dp_name] = val_str

        node = self.nodes.get(dp_name)
        if node:
            await node.set_value(ua.Variant(val_str, ua.VariantType.String))
            logger.info(f"[OPCUA] Updated {dp_name} = {val_str}")
        else:
            logger.warning(f"[OPCUA] Unknown datapoint {dp_name}, cannot update")

    # ----------------------------------------------------------------------
    # Properties
    # ----------------------------------------------------------------------
    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    async def publish_driver_state(self, state: str):
        msg = DriverConnectStatus(driver_name=self._server_name, status=state)
        if callable(self._communication_status_callback):
            await self._communication_status_callback(msg)
