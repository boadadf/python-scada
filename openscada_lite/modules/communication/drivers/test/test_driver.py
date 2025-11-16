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
import asyncio
import datetime
import inspect
from abc import ABC, abstractmethod
import threading
from typing import Dict, List, Callable, Any

from openscada_lite.common.config.config import Config
from openscada_lite.common.tracking.decorators import publish_data_flow_from_arg_async
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.models.dtos import DriverConnectStatus, RawTagUpdateMsg, CommandFeedbackMsg, SendCommandMsg
from openscada_lite.modules.communication.drivers.driver_protocol import DriverProtocol
from openscada_lite.common.models.entities import Datapoint


class TestDriver(DriverProtocol, ABC):
    def __init__(self, server_name: str):
        print(f"[INIT] Creating TestDriver {server_name}")
        self._server_name = server_name
        self._tags: Dict[str, RawTagUpdateMsg] = {}
        self._value_callback: Callable[[RawTagUpdateMsg], Any] | None = None
        self._communication_status_callback: Callable[[DriverConnectStatus], Any] | None = None
        self._command_feedback_callback: Callable[[CommandFeedbackMsg], Any] | None = None
        self._running = False
        self._connected = False
        self._task: asyncio.Task | None = None

    # -------------------------
    # Properties
    # -------------------------
    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def server_name(self) -> str:
        return self._server_name

    # -------------------------
    # Connection lifecycle
    # -------------------------
    async def connect(self):
        await self.initValues()
        self._connected = True
        if self._communication_status_callback:
            await self.publish_driver_state("online")

    async def disconnect(self):
        self._connected = False
        await self.stop_test()
        print(f"[DISCONNECT] Disconnecting driver {self._server_name}")        
        await self.publish_driver_state("offline")        

    async def initValues(self):
        now = datetime.datetime.now()
        print(f"[INIT] Initializing values for {self._server_name} tags: {self._tags}")
        for tag in self._tags.values():            
            tag.value = Config.get_instance().get_default_value(tag.datapoint_identifier)
            tag.timestamp = now
            tag.quality = "good"
            await self._publish_value(tag)

    # -------------------------
    # Subscriptions and listeners
    # -------------------------
    def subscribe(self, datapoints: List[Datapoint]):
        now = datetime.datetime.now()
        for datapoint in datapoints:
            tag_id = f"{self._server_name}@{datapoint.name}"
            self._tags[datapoint.name] = RawTagUpdateMsg(
                datapoint_identifier=tag_id,
                value=datapoint.type["default"],
                timestamp=now,
            )

    def register_value_listener(self, callback: Callable[[RawTagUpdateMsg], Any]):
        self._value_callback = callback

    def register_communication_status_listener(
        self, callback: Callable[[DriverConnectStatus], Any]
    ):
        self._communication_status_callback = callback

    def register_command_feedback(self, callback: Callable[[CommandFeedbackMsg], Any]):
        self._command_feedback_callback = callback

    # -------------------------
    # Driver interaction
    # -------------------------
    async def publish_driver_state(self, state: str):
        msg = DriverConnectStatus(driver_name=self._server_name, status=state)
        await self._safe_invoke(self._communication_status_callback, msg)

    @publish_data_flow_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def send_command(self, data: SendCommandMsg):
        if self._command_feedback_callback:
            # Remove server_name prefix if present
            if "@" in data.datapoint_identifier:
                _, dp_name = data.datapoint_identifier.split("@", 1)
            else:
                dp_name = data.datapoint_identifier

            # Check for _CMD suffix and remove it
            if dp_name.endswith("_CMD"):
                dp_name_base = dp_name[:-4]
            else:
                dp_name_base = dp_name

            exists = dp_name_base in self._tags
            full_tag_id = f"{self._server_name}@{dp_name_base}"
            value = data.value
            command_id = data.command_id
            # Start / Stop the simulation
            result = await self.handle_special_command(dp_name, value)
            if result:
                value = result

            # If the datapoint exists, publish a RawTagUpdateMsg
            if exists and self._value_callback:
                if dp_name_base in self._tags:
                    self._tags[dp_name_base].value = value
                    self._tags[dp_name_base].timestamp = datetime.datetime.now()

                tag_msg = RawTagUpdateMsg(
                    datapoint_identifier=full_tag_id,
                    value=value,
                    quality="good",
                    timestamp=datetime.datetime.now()
                )
                await self._safe_invoke(self._value_callback, tag_msg)
            
            feedback = "OK" if exists else "NOK"
            msg = CommandFeedbackMsg(
                command_id=command_id,
                datapoint_identifier=data.datapoint_identifier,
                feedback=feedback,
                value=data.value,
                timestamp=datetime.datetime.now()
            )
            await self._safe_invoke(self._command_feedback_callback, msg)            

    async def handle_special_command(self, datapoint_name: str, value: str ) -> str:
        print(f"[COMMAND] Handling special command: {datapoint_name} = {value}")
        if datapoint_name == "TEST_CMD":
            if value == "START":
                await self.start_test()
                return "STARTED"
            elif value == "STOP":
                await self.stop_test()
                return "STOPPED"
            elif value == "TOGGLE":
                if "TEST" in self._tags:
                    current_value = self._tags["TEST"].value
                    new_value = "STARTED" if current_value == "STOPPED" else "STOPPED"
                    if new_value == "STARTED":
                        await self.start_test()
                    else:
                        await self.stop_test()
                    return new_value
        elif datapoint_name in ["PUMP_CMD", "DOOR_CMD", "VALVE_CMD", "HEATER_CMD"] and value == "TOGGLE":
            base_name = datapoint_name[:-4]  # Remove _CMD
            if base_name in self._tags:
                current_value = self._tags[base_name].value
                new_value = "OPENED" if current_value == "CLOSED" else "CLOSED"
                return new_value
        elif datapoint_name in ["LEFT_SWITCH_CONTROL_CMD", "RIGHT_SWITCH_CONTROL_CMD"]:
            base_name = datapoint_name[:-4]  # Remove _CMD
            if base_name in self._tags:
                current_value = self._tags[base_name].value
                new_value = "STRAIGHT" if current_value == "TURN" else "TURN"
                return new_value

    async def start_test(self):
        if self._running:
            return
        self._running = True
        print(f"[TEST] Starting simulation loop for {self._server_name}")
        self._task = asyncio.create_task(self._publish_loop_async())

    async def stop_test(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                print(f"[TEST] Simulation loop canceled for {self._server_name}")

    async def _publish_loop_async(self):
        print(f"[TEST] Simulation loop started for {self._server_name}")
        try:
            while self._running:
                self._simulate_values()
                for tag in self._tags.values():
                    await self._publish_value(tag)
                print(f"[TEST] Published all tag values for {self._server_name}")
                await asyncio.sleep(5)
                print(f"[TEST] Simulation loop iteration complete for {self._server_name}")
        except asyncio.CancelledError:
            print(f"[DEBUG] Simulation loop canceled for {self._server_name}")
        finally:
            print(f"[TEST] Simulation loop stopped for {self._server_name}")


    # For testing: simulate a value change
    async def simulate_value(self, tag_id: str, value: Any, track_id: str):
        if self._value_callback:
            msg = RawTagUpdateMsg(
                datapoint_identifier=f"{self._server_name}@{tag_id}", value=value, track_id=track_id
            )
            await self._safe_invoke(self._value_callback, msg)

    @publish_data_flow_from_arg_async(status=DataFlowStatus.CREATED)
    async def _publish_value(self, tag: RawTagUpdateMsg):
        await self._safe_invoke(self._value_callback, tag)

    async def _publish_all(self):   
        for tag in self._tags.values():
            await self._publish_value(tag)

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
            if inspect.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            print(f"[ERROR] Exception in callback {callback}: {e}")
            raise