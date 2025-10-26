from typing import Dict
from openscada_lite.modules.communication.manager.command_listener import CommandListener
from openscada_lite.modules.communication.manager.communication_listener import CommunicationListener
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.tracking.decorators import publish_data_flow_from_arg_async
from openscada_lite.common.models.dtos import DriverConnectCommand, CommandFeedbackMsg, DriverConnectStatus, RawTagUpdateMsg, SendCommandMsg, TagUpdateMsg
from openscada_lite.modules.communication.drivers import DRIVER_REGISTRY
from openscada_lite.common.models.entities import Datapoint
from openscada_lite.modules.communication.drivers.driver_protocol import DriverProtocol
from openscada_lite.modules.communication.drivers.server_protocol import ServerProtocol
from openscada_lite.common.config.config import Config
import datetime

class ConnectorManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            raise RuntimeError("Use EventBus.get_instance() instead of direct instantiation.")
        return super().__new__(cls)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            # Temporarily allow instantiation
            cls._instance = super().__new__(cls)
            cls.__init__(cls._instance)
        return cls._instance
    
    def __init__(self):
        self.config = Config.get_instance()
        self.driver_instances: Dict[str, DriverProtocol] = {}  # key: driver name
        self.types = self.config.get_types()
        self.driver_status: Dict[str, str] = {}  # key: driver name, value: last status
        self.listener: CommunicationListener = None

        for cfg in self.config.get_drivers():
            datapoint_objs = []
            for dp in cfg.get("datapoints", []):
                name = dp["name"]
                type_ref = dp["type"]
                dp_type = self.types.get(type_ref)
                if dp_type:
                    datapoint_objs.append(Datapoint(name=name, type=dp_type))
                else:
                    print(f"WARNING: Datapoint type '{type_ref}' for '{name}' not found in dp_types config!")                        
            driver_cls = DRIVER_REGISTRY.get(cfg["driver_class"])
            if not driver_cls:
                raise ValueError(f"Unknown driver class: {cfg['driver_class']}")
            driver_instance: DriverProtocol = driver_cls(**cfg.get("connection_info", {}))
            driver_instance.initialize(cfg.get("params", {}))  # Pass params if present, else empty dict
            driver_instance.subscribe(datapoint_objs)        
            # Optionally assign datapoints to driver_instance if needed
            self.driver_instances[cfg["name"]] = driver_instance
            self.driver_status[cfg["name"]] = "offline"

    async def init_drivers(self):
        for driver in self.driver_instances.values():
            driver.register_value_listener(self.emit_value)
            driver.register_command_feedback(self.emit_command_feedback)
            await driver.register_communication_status_listener(self.emit_communication_status)

    async def forward_tag_update(self, msg: TagUpdateMsg):
        for driver in self.driver_instances.values():
            if isinstance(driver, ServerProtocol):
                await driver.handle_tag_update(msg)

    def register_listener(self, listener: CommunicationListener):
        self.listener = listener

    def set_command_listener(self, listener: CommandListener):
        # Set the command listener for all drivers that implement ServerProtocol
        for driver in self.driver_instances.values():
            if isinstance(driver, ServerProtocol):
                driver.set_command_listener(listener)

    @publish_data_flow_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def handle_driver_connect_command(self, data: DriverConnectCommand):        
        driver_name = data.driver_name
        status = data.status        
        driver = self.driver_instances.get(driver_name)        
        print(f"[CONNECT CMD] Driver '{driver_name}' -> {status} {self.driver_instances}" )
        if driver:            
            if status == "connect":                
                await driver.connect()
            elif status == "disconnect":
                await driver.disconnect()
            elif status == "toggle":
                if driver.is_connected:
                    await driver.disconnect()
                else:
                    await driver.connect()

    @publish_data_flow_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def emit_value(self, data: RawTagUpdateMsg):
        await self.listener.on_raw_tag_update(data) if self.listener else None        

    @publish_data_flow_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def emit_command_feedback(self, data: CommandFeedbackMsg):
        await self.listener.on_command_feedback(data) if self.listener else None

    @publish_data_flow_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def emit_communication_status(self, data: DriverConnectStatus):
        await self.listener.on_driver_connect_status(data) if self.listener else None
        # If the driver went offline, publish all tags as unknown
        driver_name = data.driver_name
        status = data.status
        prev_status = self.driver_status.get(driver_name)
        self.driver_status[driver_name] = status  # update status

        # Only publish unknowns if going from online to offline
        if status == "offline" and prev_status == "online":
            await self.publish_unknown_for_driver(driver_name)

    async def publish_unknown_for_driver(self, driver_name: str):
        now = datetime.datetime.now()
        datapoint_types = self.config.get_datapoint_types_for_driver(driver_name, self.types)
        for tag_name, dp_type in datapoint_types.items():
            default_value = dp_type.get("default") if dp_type and "default" in dp_type else None
            tag_msg = RawTagUpdateMsg(
                datapoint_identifier=f"{driver_name}@{tag_name}",
                value=default_value,
                quality="unknown",
                timestamp=now
            )
            await self.emit_value(tag_msg)

    async def start_all(self):
        await self.init_drivers()
        for driver in self.driver_instances.values():
            await driver.connect()

    async def stop_all(self):
        for driver in self.driver_instances.values():
            await driver.disconnect()

    @publish_data_flow_from_arg_async(status=DataFlowStatus.FORWARDED)
    async def send_command(self, data: SendCommandMsg):
        print(f"[COMMAND] Sending command: {data.datapoint_identifier} = {data.value}")
        config = Config.get_instance()
        server_id, simple_datapoint_identifier = data.datapoint_identifier.split("@", 1)

        if not config.validate_value(data.datapoint_identifier, data.value):
            # Value is invalid, send NOK feedback immediately
            feedback = CommandFeedbackMsg(
                command_id=data.command_id,
                datapoint_identifier=data.datapoint_identifier,
                value=data.value,
                feedback="NOK-wrong-value",
                timestamp=datetime.datetime.now()
            )
            await self.emit_command_feedback(feedback)
            return
        driver = self.driver_instances.get(server_id)
        if driver:
            if driver.is_connected:
                await driver.send_command(data)
            else:
                print(f"Driver '{server_id}' is not connected. Cannot send command.")
                feedback = CommandFeedbackMsg(
                    command_id=data.command_id,
                    datapoint_identifier=data.datapoint_identifier,
                    value=data.value,
                    feedback="NOK-driver-offline",
                    timestamp=datetime.datetime.now()
                )
                await self.emit_command_feedback(feedback)

    async def notify_driver_command(self, msg: SendCommandMsg):
        if self._command_listener:
            await self._command_listener.on_driver_command(msg)