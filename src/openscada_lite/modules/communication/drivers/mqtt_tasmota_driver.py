# -----------------------------------------------------------------------------
# Copyright 2026 Daniel&Hector Fernandez
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
import json
import datetime
import logging
from typing import Callable, List, Optional

import paho.mqtt.client as mqtt

from openscada_lite.common.models.dtos import (
    SendCommandMsg,
    RawTagUpdateMsg,
    DriverConnectStatus,
    CommandFeedbackMsg,
)
from openscada_lite.common.models.entities import Datapoint
from openscada_lite.modules.communication.drivers.driver_protocol import DriverProtocol


class MQTTTasmotaRelayDriver(DriverProtocol):
    def __init__(self, server_name: str) -> None:
    self._logger = logging.getLogger(__name__)
        self._server_name = server_name
        self._client: Optional[mqtt.Client] = None
        self._connected: bool = False

        # asyncio loop (captured on connect)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self._config: dict = {}
        self._device_topic: str = ""

        self._relay_mapping: dict[str, str] = {}
        self._reverse_relay_mapping: dict[str, str] = {}

        self._subscriptions: list[dict] = []
        self._publish_templates: dict = {}

        self._value_listener: Optional[Callable] = None
        self._status_listener: Optional[Callable] = None
        self._feedback_listener: Optional[Callable] = None

        # Command tracking
        self._pending_command: Optional[SendCommandMsg] = None
        self._command_timeout_task: Optional[asyncio.Task] = None
        # Track last known relay status per relay key (RELAY_1, RELAY_2)
        self._relay_status: dict[str, str] = {}

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def initialize(self, config: dict) -> None:
        self._config = config
        self._device_topic = config["device_topic"]

        self._relay_mapping = config.get("relay_mapping", {})
        self._reverse_relay_mapping = {v: k for k, v in self._relay_mapping.items()}

        self._subscriptions = config.get("subscriptions", [])
        self._publish_templates = config.get("publish", {})

    async def connect(self) -> None:
        self._loop = asyncio.get_running_loop()

        self._client = mqtt.Client(client_id=self._config.get("client_id"))

        if "username" in self._config:
            self._client.username_pw_set(
                self._config["username"],
                self._config.get("password"),
            )

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        self._client.connect(
            self._config["host"],
            self._config.get("port", 1883),
            keepalive=self._config.get("keepalive", 60),
        )

        self._client.loop_start()

    async def disconnect(self) -> None:
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()

    # --------------------------------------------------
    # Protocol-required
    # --------------------------------------------------

    def subscribe(self, datapoints: List[Datapoint]) -> None:
        # MQTT doesn't work like this
        pass

    async def send_command(self, data: SendCommandMsg) -> None:
        if not self._client or not self._loop:
            return

        identifier = data.datapoint_identifier
        dp_name = identifier.split("@", 1)[1] if "@" in identifier else identifier
        relay_key = dp_name.replace("_CMD", "")

        power = self._relay_mapping.get(relay_key)
        if not power:
            return

        template = self._publish_templates.get("command")
        if not template:
            return

        topic = template.format(
            device=self._device_topic,
            power=power,
        )

        # Handle TOGGLE: compute explicit ON/OFF based on current status
        desired_value = data.value
        if isinstance(desired_value, str) and desired_value.upper() == "TOGGLE":
            print("Current relay status:", self._relay_status)
            current = self._relay_status.get(relay_key)
            if current == "ON":
                desired_value = "OFF"
            elif current == "OFF":
                desired_value = "ON"
            else:
                desired_value = "ON"

        # Mutate the DTO so feedback reflects the effective value
        data.value = desired_value

        payload = desired_value
        if not isinstance(payload, str):
            payload = json.dumps(payload)

        # Track pending command
        self._pending_command = data

        # Cancel previous timeout (defensive)
        if self._command_timeout_task:
            self._command_timeout_task.cancel()

        timeout_seconds = self._config.get("command_timeout", 5)

        self._command_timeout_task = asyncio.create_task(
            self._command_timeout_handler(data, timeout_seconds)
        )

        self._client.publish(topic, payload, qos=1)

    def register_value_listener(self, callback: Callable) -> None:
        self._value_listener = callback

    def register_communication_status_listener(self, callback: Callable) -> None:
        self._status_listener = callback

    def register_command_feedback(self, callback: Callable) -> None:
        self._feedback_listener = callback

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def is_connected(self) -> bool:
        return self._connected

    # --------------------------------------------------
    # MQTT callbacks (Paho thread!)
    # --------------------------------------------------

    def _on_connect(self, client, userdata, flags, rc):
        self._connected = rc == 0

        for sub in self._subscriptions:
            topic = sub.get("topic", "").replace("{device}", self._device_topic)
            ttype = sub.get("type")

            if ttype == "status" and topic.endswith("POWER+"):
                for power in self._relay_mapping.values():
                    client.subscribe(f"stat/{self._device_topic}/{power}")
            else:
                client.subscribe(topic)

        if self._status_listener and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._status_listener(
                    DriverConnectStatus(
                        driver_name=self._server_name,
                        status="online",
                    )
                ),
                self._loop,
            )

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False

        if self._status_listener and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._status_listener(
                    DriverConnectStatus(
                        driver_name=self._server_name,
                        status="offline",
                    )
                ),
                self._loop,
            )

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode().upper()

        # ---- Relay status ----
        if topic.startswith(f"stat/{self._device_topic}/POWER"):
            power = topic.split("/")[-1]
            relay_key = self._reverse_relay_mapping.get(power)
            if not relay_key or not self._value_listener or not self._loop:
                return

            if payload in ("ON", "OFF"):
                # Track last known status for toggle computation
                self._relay_status[relay_key] = payload
                asyncio.run_coroutine_threadsafe(
                    self._value_listener(
                        RawTagUpdateMsg(
                            datapoint_identifier=f"{self._server_name}@{relay_key}_STATUS",
                            value=payload,
                            timestamp=datetime.datetime.now(),
                        )
                    ),
                    self._loop,
                )
            return

        # ---- Command RESULT feedback ----
        if topic == f"stat/{self._device_topic}/RESULT":
            if not self._pending_command or not self._feedback_listener or not self._loop:
                return

            cmd = self._pending_command
            self._pending_command = None

            if self._command_timeout_task:
                self._command_timeout_task.cancel()
                self._command_timeout_task = None

            asyncio.run_coroutine_threadsafe(
                self._send_command_feedback(cmd, exists=True),
                self._loop,
            )

    # --------------------------------------------------
    # Feedback + Timeout
    # --------------------------------------------------

    async def _command_timeout_handler(self, data: SendCommandMsg, timeout: int):
        try:
            await asyncio.sleep(timeout)
        except asyncio.CancelledError:
            # Task was canceled intentionally; stop execution and do not raise (NOSONAR)
            self._logger.debug("Command timeout task canceled; stopping handler.")
            return  # NOSONAR

        if self._pending_command == data:
            self._pending_command = None
            await self._send_command_feedback(data, exists=False)

    async def _send_command_feedback(self, data: SendCommandMsg, exists: bool):
        if not self._feedback_listener:
            return

        feedback = "OK" if exists else "NOK"

        msg = CommandFeedbackMsg(
            command_id=data.command_id,
            datapoint_identifier=data.datapoint_identifier,
            feedback=feedback,
            value=data.value,
            timestamp=datetime.datetime.now(),
        )

        await self._feedback_listener(msg)
