import asyncio
import datetime
import random
import time
from typing import Dict, List, Callable, Any
from app.common.models.dtos import CommunicationStatusMsg, TagUpdateMsg, CommandFeedbackMsg
from app.backend.communications.drivers.driver_protocol import DriverProtocol
from app.common.models.entities import Datapoint


class TestDriver(DriverProtocol):
    def __init__(self, server_name: str):
        print(f"[INIT] Creating TestDriver {server_name}")
        self.server_name = server_name
        self._tags: Dict[str, TagUpdateMsg] = {}
        self._value_callback: Callable[[TagUpdateMsg], Any] = None
        self._communication_status_callback: Callable[[CommunicationStatusMsg], Any] = None
        self._command_feedback_callback: Callable[[CommandFeedbackMsg], Any] = None
        self._running = False
        self._task: asyncio.Task | None = None

    def is_connected(self) -> bool:
        print(f"[CHECK] is_connected -> {self._running}")
        return self._running
    
    def server_name(self) -> str:
        return self.server_name

    async def connect(self):
        self._running = True
        # start publish loop immediately
        self._task = asyncio.create_task(self._publish_loop())
        # publish online state asynchronously without blocking
        if self._communication_status_callback:
            asyncio.create_task(
                self.publish_driver_state("online")
        )

    async def publish_driver_state(self, state: str):
        print(f"[STATE] Publishing driver {self.server_name} as {state}")
        if self._communication_status_callback:
            print(f"[STATE] Calling communication_status_callback for {self.server_name}")
            await self._communication_status_callback(CommunicationStatusMsg(
                server_name=self.server_name,
                status=state
            ))

    async def disconnect(self):
        print(f"[DISCONNECT] Disconnecting driver {self.server_name}")
        self._running = False
        await self.publish_driver_state("offline")
        if self._task:
            print(f"[DISCONNECT] Waiting for publish loop to exit...")
            await self._task
            print(f"[DISCONNECT] Publish loop exited cleanly")

    def subscribe(self, datapoints: List[Datapoint]):
        print(f"[SUBSCRIBE] Subscribing {len(datapoints)} datapoints")
        now = datetime.datetime.now()
        for datapoint in datapoints:
            tag_id = f"{self.server_name}@{datapoint.name}"
            print(f"[SUBSCRIBE] Adding {tag_id} with default {datapoint.type['default']}")
            self._tags[datapoint.name] = TagUpdateMsg(
                datapoint_identifier=tag_id,
                value=datapoint.type["default"],
                timestamp=now,
            )

    def register_value_listener(self, callback: Callable[[TagUpdateMsg], Any]):
        print(f"[REGISTER] Value listener registered")
        self._value_callback = callback

    async def register_communication_status_listener(self, callback: Callable[[CommunicationStatusMsg], Any]):
        print(f"[REGISTER] Communication status listener registered")
        self._communication_status_callback = callback
        publish_state = "online" if self._running else "offline"
        await self.publish_driver_state(publish_state)

    def register_command_feedback(self, callback: Callable[[CommandFeedbackMsg], Any]):
        print(f"[REGISTER] Command feedback listener registered")
        self._command_feedback_callback = callback

    async def send_command(self, tag_id: str, command: Any, command_id: str):
        print(f"[COMMAND] Sending command {command_id} to {tag_id} with payload={command}")
        await asyncio.sleep(0.1)
        if self._command_feedback_callback:
            full_tag_id = f"{self.server_name}@{tag_id}"
            print(f"[COMMAND] Command complete, calling feedback callback for {full_tag_id}")
            await self._command_feedback_callback(CommandFeedbackMsg(
                command_id=command_id,
                datapoint_identifier=full_tag_id,
                status="OK"
            ))

    async def _publish_loop(self):
        print(f"[LOOP] Publish loop started")
        try:
            while self._running:
                for tag in self._tags.values():
                    tag.value = random.random() * 100
                    tag.timestamp = datetime.datetime.now()
                    print(f"[LOOP] Publishing {tag.datapoint_identifier} = {tag.value}")
                    if self._value_callback:
                        print(f"[LOOP] About to call value_callback for {tag.datapoint_identifier}")
                        await self._value_callback(tag)
                        print(f"[LOOP] Returned from value_callback for {tag.datapoint_identifier}")
                    print(f"[LOOP] Done publishing {tag.datapoint_identifier}")
                print(f"[LOOP] Sleeping before next publish cycle")
                time.sleep(1)
            print(f"[LOOP] Exiting publish loop")
        except Exception as e:
            print(f"[ERROR] Exception in _publish_loop: {e}")
            print(f"[ERROR] Last tag = {tag.datapoint_identifier}")
