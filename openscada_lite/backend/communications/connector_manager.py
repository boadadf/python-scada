from typing import Any, Dict
from openscada_lite.common.models.dtos import DriverConnectCommand
from openscada_lite.backend.communications.drivers import DRIVER_REGISTRY
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.models.entities import Datapoint
from openscada_lite.backend.communications.drivers.driver_protocol import DriverProtocol
from openscada_lite.common.config.config import Config

class ConnectorManager:
    def __init__(self, event_bus: EventBus):
        config = Config.get_instance()
        self.event_bus = event_bus
        self.event_bus.subscribe(EventType.DRIVER_CONNECT_COMMAND, self.handle_driver_connect)
        self.driver_instances: Dict[str, DriverProtocol] = {}  # key: driver name
        self.types = config.get_types()

        for cfg in config.get_drivers():
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
            driver_instance.subscribe(datapoint_objs)        
            # Optionally assign datapoints to driver_instance if needed
            self.driver_instances[cfg["name"]] = driver_instance


    async def init_drivers(self):
        for driver in self.driver_instances.values():
            driver.register_value_listener(self.emit_value)
            driver.register_command_feedback(self.emit_command_feedback)
            await driver.register_communication_status_listener(self.emit_communication_status)

    async def handle_driver_connect(self, data: DriverConnectCommand):
        print(f"[CONNECT MANAGER] Handling driver connect command: {data}")
        driver_name = data.driver_name
        status = data.status
        driver = self.driver_instances.get(driver_name)
        if driver:
            if status == "connect":
                await driver.connect()
            elif status == "disconnect":
                await driver.disconnect()

    async def emit_value(self, data: dict):
        await self.event_bus.publish(EventType.RAW_TAG_UPDATE, data)

    async def emit_command_feedback(self, data: dict):
        await self.event_bus.publish(EventType.COMMAND_FEEDBACK, data)

    async def emit_communication_status(self, data: dict):
        await self.event_bus.publish(EventType.DRIVER_CONNECT_STATUS, data)

    async def start_all(self):
        await self.init_drivers()
        for driver in self.driver_instances.values():
            await driver.connect()

    async def stop_all(self):
        for driver in self.driver_instances.values():
            await driver.disconnect()

    async def send_command(self, server_id: str, tag_id: str, command: Any, command_id: str):
        driver = self.driver_instances.get(server_id)
        if driver:
            await driver.send_command(tag_id, command, command_id)