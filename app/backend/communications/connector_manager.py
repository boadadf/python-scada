import asyncio
from typing import Any
from app.backend.communications.drivers import DRIVER_REGISTRY
from app.common.bus.event_types import EventType
from app.common.bus.event_bus import EventBus

class ConnectorManager:
    def __init__(self, event_bus: EventBus, drivers_config: list):
        self.event_bus = event_bus
        self.event_bus.subscribe(EventType.DRIVER_CONNECT, self.handle_driver_connect)
        self.drivers = []
        for cfg in drivers_config:
            print(f"Loading driver config: {cfg}")
            driver_class_name = cfg["driver_class"]
            driver_cls = DRIVER_REGISTRY.get(driver_class_name)
            if not driver_cls:
                raise ValueError(f"Unknown driver class: {driver_class_name}")
            driver_instance = driver_cls(**cfg.get("connection_info", {}))
            driver_name = cfg["name"]
            self.drivers.append({
                "driver": driver_instance,
                "datapoints": cfg.get("datapoints", [])
            })
            print(f"Driver {driver_name} of class {driver_class_name} loaded")

    async def init_drivers(self):
        for d in self.drivers:            
            await d["driver"].register_value_listener(self.emit_value)            
            await d["driver"].register_command_feedback(self.emit_command_feedback)
            await d["driver"].register_communication_status_listener(self.emit_communication_status)
            await d["driver"].subscribe(d["datapoints"])

    async def handle_driver_connect(self, data):
        driver_name = data["server_name"]
        status = data["status"]
        for d in self.drivers:
            if getattr(d["driver"], "server_name", None) == driver_name:
                #TODO: Handle already connected/disconnected states
                #TODO: The connect/disconnect should be sent from the driver
                #TODO: Is there a way to have an interface for Driver?
                if status == "connect":
                    await d["driver"].connect()
                elif status == "disconnect":
                    await d["driver"].disconnect()
                # Publish status after action
                break

    async def emit_value(self, data: dict):
        await self.event_bus.publish(EventType.RAW_TAG_UPDATE, data)

    async def emit_command_feedback(self, data: dict):
        await self.event_bus.publish(EventType.COMMAND_FEEDBACK, data)

    async def emit_communication_status(self, data: dict):
        await self.event_bus.publish(EventType.DRIVER_CONNECT_STATUS, data)

    #For testing purposes
    async def start_all(self):
        await self.init_drivers()
        for d in self.drivers:            
            await d["driver"].connect()            

    async def stop_all(self):
        for d in self.drivers:
            await d["driver"].disconnect()

    async def send_command(self, server_id: str, tag_id: str, command: Any, command_id: str):
        # Find driver by tag namespace
        for d in self.drivers:
            if d["driver"].server_name == server_id:
                await d["driver"].send_command(tag_id, command, command_id)
                break