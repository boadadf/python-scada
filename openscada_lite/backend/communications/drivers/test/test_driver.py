import asyncio
import datetime
import inspect
from abc import ABC, abstractmethod
import threading
from typing import Dict, List, Callable, Any

from openscada_lite.common.models.dtos import DriverConnectStatus, TagUpdateMsg, CommandFeedbackMsg
from openscada_lite.backend.communications.drivers.driver_protocol import DriverProtocol
from openscada_lite.common.models.entities import Datapoint


class TestDriver(DriverProtocol, ABC):
    def __init__(self, server_name: str):
        print(f"[INIT] Creating TestDriver {server_name}")
        self._server_name = server_name
        self._tags: Dict[str, TagUpdateMsg] = {}
        self._value_callback: Callable[[TagUpdateMsg], Any] | None = None
        self._communication_status_callback: Callable[[DriverConnectStatus], Any] | None = None
        self._command_feedback_callback: Callable[[CommandFeedbackMsg], Any] | None = None
        self._running = False
        self._task: asyncio.Task | None = None

    # -------------------------
    # Properties
    # -------------------------
    @property
    def is_connected(self) -> bool:
        return self._running

    @property
    def server_name(self) -> str:
        return self._server_name

    # -------------------------
    # Connection lifecycle
    # -------------------------
    async def connect(self):
        self._running = True
        def runner():
            asyncio.run(self._publish_loop())  # runs its own loop
        thread = threading.Thread(target=runner, daemon=True)
        thread.start()
        if self._communication_status_callback:
            await self.publish_driver_state("online")
        

    async def disconnect(self):
        print(f"[DISCONNECT] Disconnecting driver {self._server_name}")
        self._running = False
        await self.publish_driver_state("offline")
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                print(f"[DISCONNECT] Publish loop cancelled cleanly")

    # -------------------------
    # Subscriptions and listeners
    # -------------------------
    def subscribe(self, datapoints: List[Datapoint]):
        now = datetime.datetime.now()
        for datapoint in datapoints:
            tag_id = f"{self._server_name}@{datapoint.name}"
            self._tags[datapoint.name] = TagUpdateMsg(
                datapoint_identifier=tag_id,
                value=datapoint.type["default"],
                timestamp=now,
            )

    def register_value_listener(self, callback: Callable[[TagUpdateMsg], Any]):
        self._value_callback = callback

    async def register_communication_status_listener(
        self, callback: Callable[[DriverConnectStatus], Any]
    ):
        self._communication_status_callback = callback
        publish_state = "online" if self._running else "offline"
        await self.publish_driver_state(publish_state)

    def register_command_feedback(self, callback: Callable[[CommandFeedbackMsg], Any]):
        self._command_feedback_callback = callback

    # -------------------------
    # Driver interaction
    # -------------------------
    async def publish_driver_state(self, state: str):
        msg = DriverConnectStatus(driver_name=self._server_name, status=state)
        await self._safe_invoke(self._communication_status_callback, msg)

    async def send_command(self, datapoint_identifier: str, value: str, command_id: str):
        if self._command_feedback_callback:
            full_tag_id = f"{self._server_name}@{datapoint_identifier}"
            msg = CommandFeedbackMsg(
                command_id=command_id,
                datapoint_identifier=full_tag_id,
                feedback="OK",
                value=value,
                timestamp=datetime.datetime.now()
            )
            await self._safe_invoke(self._command_feedback_callback, msg)

    async def simulate_value(self, tag_id: str, value: Any):
        if self._value_callback:
            msg = TagUpdateMsg(
                datapoint_identifier=f"{self._server_name}@{tag_id}", value=value
            )
            await self._safe_invoke(self._value_callback, msg)

    # -------------------------
    # Background publishing loop
    # -------------------------
    async def _publish_loop(self):
        try:
            while self._running:
                await self._simulate_values()
                for tag in self._tags.values():
                    await self._safe_invoke(self._value_callback, tag)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            print(f"[PUBLISH LOOP] Cancelled for {self._server_name}")
        except Exception as e:
            print(f"[ERROR] Exception in _publish_loop: {e}")
            raise

    @abstractmethod
    async def _simulate_values(self):
        pass

    # -------------------------
    # Helper
    # -------------------------
    async def _safe_invoke(self, callback, *args, **kwargs):
        if not callback:
            return
        try:
            result = callback(*args, **kwargs)
            if inspect.iscoroutine(result):
                await result
        except Exception as e:
            print(f"[ERROR] Exception in callback {callback}: {e}")
            raise