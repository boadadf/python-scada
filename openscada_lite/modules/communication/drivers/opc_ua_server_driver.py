import re
from opcua import Server, ua
from openscada_lite.modules.communication.drivers.server_protocol import ServerProtocol
from openscada_lite.common.models.dtos import TagUpdateMsg, SendCommandMsg

class OPCUAServerDriver(ServerProtocol):
    """
    OPC UA Server Driver that exposes datapoints as OPC UA nodes.
    Nodes matching allow_write_regex (default: *_CMD) are writable.
    When a writable node is written, a SendCommandMsg is sent to the command listener.
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

    def set_command_listener(self, listener) -> None:
        self._command_listener = listener

    def initialize(self, config: dict) -> None:
        self.namespace_url = config.get("namespaceurl", "http://default.namespace")
        self.allow_write_regex = re.compile(config.get("allow_write_regex", ".*_CMD$"))
        self.endpoint = config.get("endpoint", self.endpoint)
        # Register namespace here
        self.namespace_index = self.server.register_namespace(self.namespace_url)

    async def connect(self) -> None:
        self.server.set_endpoint(self.endpoint)
        self.namespace_index = self.server.register_namespace(self.namespace_url)
        self.server.start()
        self._is_connected = True
        print(f"OPC UA Server started at {self.endpoint} with namespace {self.namespace_url}")

    async def disconnect(self) -> None:
        self.server.stop()
        self._is_connected = False
        print("OPC UA Server stopped.")

    def subscribe(self, datapoints: list) -> None:
        """
        Expose datapoints as OPC UA nodes.
        """
        objects = self.server.get_objects_node()
        for dp in datapoints:
            writable = bool(self.allow_write_regex.match(dp.name))
            node = objects.add_variable(self.namespace_index, dp.name, 0)
            node.set_writable(writable)
            self.nodes[dp.name] = node
            if writable:
                self._register_write_handler(node, dp.name)
        print(f"Exposed {len(datapoints)} nodes in OPC UA server.")

    def _register_write_handler(self, node, dp_name):
        # Handler for OPC UA write events
        original_set_value = node.set_value

        def set_value_hook(value):
            # Call the original set_value
            original_set_value(value)
            # Send SendCommandMsg to the command listener
            if self._command_listener:
                msg = SendCommandMsg(
                    datapoint_identifier=f"{self.server_name}@{dp_name}",
                    value=value
                )
                # Schedule publish on event loop
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._command_listener.on_driver_command(msg))
                else:
                    asyncio.run(self._command_listener.on_driver_command(msg))

        node.set_value = set_value_hook

    async def handle_tag_update(self, msg: TagUpdateMsg) -> None:
        """
        Update OPC UA node value when a TagUpdateMsg is received.
        """
        dp_name = msg.datapoint_identifier.split("@")[-1]
        node = self.nodes.get(dp_name)
        if node:
            node.set_value(msg.value)

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def is_connected(self) -> bool:
        return self._is_connected