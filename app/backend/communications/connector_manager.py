import asyncio
from typing import Any
from backend.communications.drivers import DRIVER_REGISTRY
from common.bus.event_types import COMMAND_FEEDBACK, RAW_TAG_UPDATE, TAG_UPDATE

class ConnectorManager:
    def __init__(self, event_bus, drivers_config: list):
        self.event_bus = event_bus
        self.drivers = []
        for cfg in drivers_config:
            driver_class_name = cfg["driver_class"]
            driver_cls = DRIVER_REGISTRY.get(driver_class_name)
            if not driver_cls:
                raise ValueError(f"Unknown driver class: {driver_class_name}")
            driver_instance = driver_cls(**cfg.get("connection_info", {}))
            driver_name = cfg["name"]
            # Do NOT register async listeners here!
            self.drivers.append({
                "driver": driver_instance,
                "datapoints": cfg.get("datapoints", [])
            })

    async def emit_value(self, data: dict):
        await self.event_bus.publish(RAW_TAG_UPDATE, data)

    async def emit_command_feedback(self, data: dict):
        await self.event_bus.publish(COMMAND_FEEDBACK, data)

    async def start_all(self):
        for d in self.drivers:            
            await d["driver"].register_value_listener(self.emit_value)
            
            await d["driver"].register_command_feedback(self.emit_command_feedback)

            await d["driver"].connect()
            await d["driver"].subscribe(d["datapoints"])

    async def stop_all(self):
        for d in self.drivers:
            await d["driver"].disconnect()

    async def send_command(self, server_id: str, tag_id: str, command: Any, command_id: str):
        # Find driver by tag namespace
        for d in self.drivers:
            if d["driver"].server_name == server_id:
                await d["driver"].send_command(tag_id, command, command_id)
                break