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


class OPCUAServerDriver(ServerProtocol):
    """
    Async OPC UA Server driver:
      ✅ Exposes datapoints as writable OPC UA variables.
      ✅ Captures every client write using subscriptions.
      ✅ Updates node values asynchronously.
    """

    def __init__(self, server_name="OPCUAServer", **kwargs):
        self._server_name = server_name
        self.server = Server()
        self.namespace_index = None
        self.namespace_url = None
        self.nodes = {}
        self.allow_write_regex = None
        self.endpoint = "opc.tcp://0.0.0.0:4840/freeopcua/server/"
        self._is_connected = False
        self._command_listener = None
        self._communication_status_callback = None
        self.subscription: Subscription | None = None
        self._nodes: dict[str, str] = {}

    # ----------------------------------------------------------------------
    # Initialization
    # ----------------------------------------------------------------------
    def set_command_listener(self, listener) -> None:
        self._command_listener = listener

    def initialize(self, config: dict) -> None:
        """Prepare OPC UA namespace and regex config (sync)."""
        self.namespace_url = config.get("namespaceurl", "http://default.namespace")  # NOSONAR
        self.allow_write_regex = re.compile(config.get("allow_write_regex", ".*_CMD$"))
        self.endpoint = config.get("endpoint", self.endpoint)

    def subscribe(self, datapoints: list) -> None:
        """Store datapoints; actual node creation happens in connect()."""
        for dp in datapoints:
            # Use a unique, hashable attribute of Datapoint as the key
            self._nodes[dp.name] = None  # Assuming `dp.name` is a unique string
        print(f"[OPCUA] Will expose {len(datapoints)} nodes on connect()")

    # ----------------------------------------------------------------------
    # Connection / server lifecycle
    # ----------------------------------------------------------------------
    async def connect(self) -> None:
        """Initialize and start server, create nodes, and set up write monitoring."""
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name(self._server_name)

        # Initialize asyncua server
        await self.server.init()

        # Register namespace (async)
        self.namespace_index = await self.server.register_namespace(self.namespace_url)

        # Create nodes
        await self._create_nodes()

        # Start server
        await self.server.start()

        # Create subscription for capturing client writes
        self.subscription = await self.server.create_subscription(100, self)
        await self._setup_write_monitors()

        self._is_connected = True
        if self._communication_status_callback:
            await self.publish_driver_state("online")

        print(
            f"[OPCUA] Server started at {self.endpoint} "
            f"(namespace: {self.namespace_url}, index: {self.namespace_index})"
        )

    async def disconnect(self) -> None:
        """Stop the server and clean up."""
        if self.subscription:
            await self.subscription.delete()
            self.subscription = None

        try:
            await self.server.stop()
        except Exception as e:
            print(f"[WARN] Error stopping server: {e}")

        self._is_connected = False
        if self._communication_status_callback:
            await self.publish_driver_state("offline")
        print("[OPCUA] Server stopped")

    # ----------------------------------------------------------------------
    # Node creation
    # ----------------------------------------------------------------------
    async def _create_nodes(self):
        """Create OPC UA variables for all datapoints."""
        objects = self.server.get_objects_node()

        for datapoint in self._nodes.keys():
            writable = bool(self.allow_write_regex.match(datapoint))
            initial_value = self._nodes.get(datapoint, "")

            node = await objects.add_variable(
                self.namespace_index, datapoint, ua.Variant(initial_value, ua.VariantType.String)
            )

            if writable:
                await node.set_writable()
                # Update masks so UA Expert sees the node as writable
                await node.write_attribute(
                    ua.AttributeIds.UserWriteMask, ua.DataValue(ua.UInt32(1))
                )
                await node.write_attribute(ua.AttributeIds.WriteMask, ua.DataValue(ua.UInt32(1)))

            self.nodes[datapoint] = node

        print(f"[OPCUA] Created {len(self._nodes)} nodes")

    # ----------------------------------------------------------------------
    # Write monitoring
    # ----------------------------------------------------------------------
    async def _setup_write_monitors(self):
        """Attach data change subscriptions to all writable nodes."""
        if not self.subscription:
            print("[WARN] Subscription not initialized for write monitoring")
            return

        for dp_name, node in self.nodes.items():
            if self.allow_write_regex.match(dp_name):
                await self.subscription.subscribe_data_change(node)
        print(f"[OPCUA] Write monitoring enabled for {len(self.nodes)} nodes")

    async def datachange_notification(self, node, val, data):
        """Called by asyncua subscription when a client writes a node."""
        dp_name = next((n for n, nd in self.nodes.items() if nd.nodeid == node.nodeid), None)
        if dp_name:
            val_str = str(val)
            print(f"[WRITE] Client wrote {dp_name} -> '{val_str}'")
            if self._command_listener:
                msg = SendCommandMsg(
                    datapoint_identifier=dp_name, value=val_str, command_id=str(uuid.uuid4())
                )
                await self._command_listener.on_driver_command(msg)

    # ----------------------------------------------------------------------
    # Tag updates from internal system
    # ----------------------------------------------------------------------
    async def handle_tag_update(self, msg: TagUpdateMsg) -> None:
        """Update OPC UA node value asynchronously when internal tag changes."""
        dp_name = msg.datapoint_identifier
        val_str = str(msg.value)
        self._nodes[dp_name] = val_str

        node = self.nodes.get(dp_name)
        if node:
            await node.set_value(ua.Variant(val_str, ua.VariantType.String))
            print(f"[OPCUA] Updated {dp_name} = {val_str}")
        else:
            print(f"[OPCUA] Unknown datapoint {dp_name}, cannot update node")

    # ----------------------------------------------------------------------
    # Communication status
    # ----------------------------------------------------------------------
    def register_communication_status_listener(self, callback):
        self._communication_status_callback = callback

    async def publish_driver_state(self, state: str):
        msg = DriverConnectStatus(driver_name=self._server_name, status=state)
        if callable(self._communication_status_callback):
            await self._communication_status_callback(msg)

    # ----------------------------------------------------------------------
    # Properties
    # ----------------------------------------------------------------------
    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def is_connected(self) -> bool:
        return self._is_connected
