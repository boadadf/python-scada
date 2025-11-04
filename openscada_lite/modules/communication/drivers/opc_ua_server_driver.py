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
import asyncio
from opcua import Server, ua
from openscada_lite.modules.communication.drivers.server_protocol import ServerProtocol
from openscada_lite.common.models.dtos import DriverConnectStatus, TagUpdateMsg, SendCommandMsg


class OPCUAServerDriver(ServerProtocol):
    """
    OPC UA Server driver that:
      ✅ Exposes datapoints as writable OPC UA variables.
      ✅ Reacts to *every* client write (even if the value doesn’t change).
      ✅ Converts all values to string before sending SendCommandMsg.
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
        self._pending_datapoints = []
        self._original_write_attribute = None  # hook to restore later

    # ----------------------------------------------------------------------
    # Initialization and connection
    # ----------------------------------------------------------------------
    def set_command_listener(self, listener) -> None:
        self._command_listener = listener

    def initialize(self, config: dict) -> None:
        """Prepare OPC UA namespace and config."""
        self.namespace_url = config.get("namespaceurl", "http://default.namespace")
        self.allow_write_regex = re.compile(config.get("allow_write_regex", ".*_CMD$"))
        self.endpoint = config.get("endpoint", self.endpoint)
        self.namespace_index = self.server.register_namespace(self.namespace_url)

    def subscribe(self, datapoints: list) -> None:
        """Expose all datapoints as variables (before server start)."""
        self._pending_datapoints = datapoints
        objects = self.server.get_objects_node()
        for dp in datapoints:
            writable = bool(self.allow_write_regex.match(dp.name))
            node = objects.add_variable(self.namespace_index, dp.name, ua.Variant("", ua.VariantType.String))
            node.set_writable(writable)
            self.nodes[dp.name] = node
        print(f"[OPCUA] Exposed {len(datapoints)} nodes in OPC UA server")

    async def connect(self) -> None:
        """Start the OPC UA server and hook into write operations."""
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name(self._server_name)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.server.start)

        # Patch server’s write handler to detect all client writes
        self._patch_write_handler()

        self._is_connected = True
        if self._communication_status_callback:
            await self.publish_driver_state("online")

        print(f"[OPCUA] Server started at {self.endpoint} (namespace: {self.namespace_url})")

    async def disconnect(self) -> None:
        """Stop the server and restore original handler."""
        if self._original_write_attribute:
            self.server.iserver.write_attribute = self._original_write_attribute
            self._original_write_attribute = None

        try:
            await asyncio.get_event_loop().run_in_executor(None, self.server.stop)
        except Exception as e:
            print(f"[WARN] Error stopping server: {e}")

        self._is_connected = False
        if self._communication_status_callback:
            await self.publish_driver_state("offline")
        print("[OPCUA] Server stopped")

    # ----------------------------------------------------------------------
    # Handling incoming tag updates from internal system
    # ----------------------------------------------------------------------
    async def handle_tag_update(self, msg: TagUpdateMsg) -> None:
        """Update server node value when internal tag changes."""
        dp_name = msg.datapoint_identifier
        node = self.nodes.get(dp_name)
        if node:
            val_str = str(msg.value)
            node.set_value(ua.Variant(val_str, ua.VariantType.String))
            print(f"[OPCUA] Updated {dp_name} = {val_str}")

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
    # Internal write hook
    # ----------------------------------------------------------------------
    def _patch_write_handler(self):
        """Monkey-patch the internal write method to detect every client write."""
        if not hasattr(self.server, "iserver") or not hasattr(self.server.iserver, "write_attribute"):
            print("[WARN] Cannot patch write_attribute (server not started yet?)")
            return

        self._original_write_attribute = self.server.iserver.write_attribute
        orig_write = self._original_write_attribute

        def patched_write(nodeid, attributeid, datavalue):
            try:
                val = datavalue.Value.Value
                dp_name = next((n for n, node in self.nodes.items() if node.nodeid == nodeid), None)

                if dp_name and self.allow_write_regex.match(dp_name):
                    val_str = str(val)
                    msg = SendCommandMsg(
                        datapoint_identifier=dp_name,
                        value=val_str,
                        command_id=str(uuid.uuid4())
                    )
                    print(f"[WRITE] Client wrote {dp_name} -> '{val_str}'")

                    if self._command_listener:
                        asyncio.create_task(self._command_listener.on_driver_command(msg))
            except Exception as e:
                print(f"[ERROR] Intercept write failed: {e}")

            # Always perform the real write
            return orig_write(nodeid, attributeid, datavalue)

        self.server.iserver.write_attribute = patched_write
        print("[OPCUA] Write interception active (every client write will be detected)")

    # ----------------------------------------------------------------------
    # Properties
    # ----------------------------------------------------------------------
    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def is_connected(self) -> bool:
        return self._is_connected
