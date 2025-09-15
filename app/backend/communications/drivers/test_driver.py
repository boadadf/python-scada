import asyncio
import random
from typing import List, Callable, Any
from app.common.models.dtos import TagUpdateMsg, CommandFeedbackMsg

class TestDriver:
    def __init__(self, server_name: str):
        self.server_name = server_name
        self._datapoints: List[str] = []
        self._value_callback: Callable[[TagUpdateMsg], Any] = None
        self._command_feedback_callback: Callable[[CommandFeedbackMsg], Any] = None
        self._running = False

    async def connect(self):
        self._running = True
        print(f"TestDriver {self.server_name} connected")

    async def disconnect(self):
        self._running = False
        print(f"TestDriver {self.server_name} disconnected")

    async def subscribe(self, datapoints: List[str]):
        self._datapoints = datapoints
        asyncio.create_task(self._publish_loop())

    async def register_value_listener(self, callback: Callable[[TagUpdateMsg], Any]):
        self._value_callback = callback

    async def simulate_value(self, tag_id: str, value: Any):
        """Simulate the driver receiving a new datapoint value."""
        if self._value_callback:
            await self._value_callback(TagUpdateMsg(tag_id=f"{self.server_name}@{tag_id}", value=value))

    async def register_command_feedback(self, callback: Callable[[CommandFeedbackMsg], Any]):
        self._command_feedback_callback = callback

    async def send_command(self, tag_id: str, command: Any, command_id: str):
        await asyncio.sleep(0.1)
        if self._command_feedback_callback:
            full_tag_id = f"{self.server_name}@{tag_id}"
            await self._command_feedback_callback(CommandFeedbackMsg(
                command_id= command_id,
                tag_id=full_tag_id,
                status="OK"
            ))

    async def _publish_loop(self):
        while self._running:
            for tag_id in self._datapoints:
                value = random.random() * 100
                full_tag_id = f"{self.server_name}@{tag_id}"
                if self._value_callback:
                    await self._value_callback(TagUpdateMsg(tag_id=full_tag_id, value=value))
            await asyncio.sleep(1)

