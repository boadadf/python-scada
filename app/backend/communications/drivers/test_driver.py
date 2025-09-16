import asyncio
import random
from tkinter import EventType
from typing import List, Callable, Any
from app.common.models.dtos import CommunicationStatusMsg, TagUpdateMsg, CommandFeedbackMsg
from app.backend.communications.drivers.driver_abs import Driver

class TestDriver(Driver):
    def __init__(self, server_name: str):
        self.server_name = server_name
        self._datapoints: List[str] = []
        self._value_callback: Callable[[TagUpdateMsg], Any] = None
        self._communication_status_callback: Callable[[CommunicationStatusMsg], Any] = None
        self._command_feedback_callback: Callable[[CommandFeedbackMsg], Any] = None
        self._running = False

    def is_connected(self) -> bool:
        return self._running
    
    def server_name(self) -> str:
        return self.server_name

    async def connect(self):
        self._running = True
        print(f"TestDriver {self.server_name} connected")
        await self.publish_driver_state("online")
 
    async def publish_driver_state(self, state: str):
        print(f"Publishing driver {self.server_name} as {state}")
        if self._communication_status_callback:
            await self._communication_status_callback(CommunicationStatusMsg(
                server_name=self.server_name,
                status=state
            ))

    async def disconnect(self):
        self._running = False
        print(f"TestDriver {self.server_name} disconnected")
        await self.publish_driver_state("offline")

    async def subscribe(self, datapoints: List[str]):
        self._datapoints = datapoints
        asyncio.create_task(self._publish_loop())

    async def register_value_listener(self, callback: Callable[[TagUpdateMsg], Any]):
        self._value_callback = callback

    async def register_communication_status_listener(self, callback: Callable[[CommunicationStatusMsg], Any]):
        self._communication_status_callback = callback
        publish_state = "online" if self._running else "offline"
        await self.publish_driver_state(publish_state)

    async def simulate_value(self, tag_id: str, value: Any):
        """Simulate the driver receiving a new datapoint value."""
        if self._value_callback:
            await self._value_callback(TagUpdateMsg(datapoint_identifier=f"{self.server_name}@{tag_id}", value=value))

    async def register_command_feedback(self, callback: Callable[[CommandFeedbackMsg], Any]):
        self._command_feedback_callback = callback

    async def send_command(self, tag_id: str, command: Any, command_id: str):
        await asyncio.sleep(0.1)
        if self._command_feedback_callback:
            full_tag_id = f"{self.server_name}@{tag_id}"
            await self._command_feedback_callback(CommandFeedbackMsg(
                command_id= command_id,
                datapoint_identifier=full_tag_id,
                status="OK"
            ))

    async def _publish_loop(self):
        while self._running:
            for tag_id in self._datapoints:
                value = random.random() * 100
                full_tag_id = f"{self.server_name}@{tag_id}"
                if self._value_callback:
                    await self._value_callback(TagUpdateMsg(datapoint_identifier=full_tag_id, value=value))
            await asyncio.sleep(1)