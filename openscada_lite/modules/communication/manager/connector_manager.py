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

from typing import Dict
from openscada_lite.modules.communication.drivers.test.test_driver import TestDriver
from openscada_lite.modules.communication.manager.command_listener import (
    CommandListener,
)
from openscada_lite.modules.communication.manager.communication_listener import (
    CommunicationListener,
)
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.tracking.decorators import publish_from_arg_async
from openscada_lite.common.models.dtos import (
    DriverConnectCommand,
    CommandFeedbackMsg,
    DriverConnectStatus,
    RawTagUpdateMsg,
    SendCommandMsg,
    TagUpdateMsg,
)
from openscada_lite.modules.communication.drivers import DRIVER_REGISTRY
from openscada_lite.common.models.entities import Datapoint
from openscada_lite.modules.communication.drivers.driver_protocol import DriverProtocol
from openscada_lite.modules.communication.drivers.server_protocol import ServerProtocol
from openscada_lite.common.config.config import Config
import datetime
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


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
        self.driver_instances: Dict[str, DriverProtocol] = {}
        self.types = self.config.get_types()
        self.driver_status: Dict[str, str] = {}
        self.listener: CommunicationListener = None
        self.datapoint_to_drivers: Dict[str, set] = defaultdict(set)

        for cfg in self.config.get_drivers():
            datapoint_objs = []
            for dp in cfg.get("datapoints", []):
                name = dp["name"]
                type_ref = dp["type"]
                dp_type = self.types.get(type_ref)
                if dp_type:
                    datapoint_objs.append(Datapoint(name=name, type=dp_type))
                else:
                    logger.warning(
                        f"Datapoint type '{type_ref}' "
                        f"for '{name}' not found in dp_types config!"
                    )
            driver_cls = DRIVER_REGISTRY.get(cfg["driver_class"])
            if not driver_cls:
                raise ValueError(f"Unknown driver class: {cfg['driver_class']}")
            driver_instance: DriverProtocol = driver_cls(**cfg.get("connection_info", {}))
            driver_instance.initialize(cfg.get("params", {}))
            driver_instance.subscribe(datapoint_objs)
            self.driver_instances[cfg["name"]] = driver_instance
            self.driver_status[cfg["name"]] = "offline"

            # Register datapoints for this driver
            for dp in datapoint_objs:
                # Use full identifier: driver_name@datapoint_name
                full_id = f"{cfg['name']}@{dp.name}"
                self.datapoint_to_drivers[full_id].add(driver_instance)

    async def init_drivers(self):
        for driver in self.driver_instances.values():
            driver.register_value_listener(self.emit_value)
            driver.register_command_feedback(self.emit_command_feedback)
            driver.register_communication_status_listener(self.emit_communication_status)
            await self.emit_communication_status(
                DriverConnectStatus(driver_name=driver.server_name, status="offline")
            )

    async def forward_tag_update(self, msg: TagUpdateMsg):
        # Notify only drivers interested in this datapoint
        for driver in self.datapoint_to_drivers.get(msg.datapoint_identifier, []):
            if isinstance(driver, ServerProtocol):
                await driver.handle_tag_update(msg)

    def register_listener(self, listener: CommunicationListener):
        self.listener = listener

    def set_command_listener(self, listener: CommandListener):
        # Set the command listener for all drivers that implement ServerProtocol
        for driver in self.driver_instances.values():
            if isinstance(driver, ServerProtocol):
                driver.set_command_listener(listener)

    @publish_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def handle_driver_connect_command(self, data: DriverConnectCommand):
        driver_name = data.driver_name
        status = data.status
        driver = self.driver_instances.get(driver_name)
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

    @publish_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def emit_value(self, data: RawTagUpdateMsg):
        await self.listener.on_raw_tag_update(data) if self.listener else None

    @publish_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def emit_command_feedback(self, data: CommandFeedbackMsg):
        await self.listener.on_command_feedback(data) if self.listener else None

    @publish_from_arg_async(status=DataFlowStatus.RECEIVED)
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
                timestamp=now,
            )
            await self.emit_value(tag_msg)

    async def start_all(self):
        await self.init_drivers()
        for driver in self.driver_instances.values():
            if isinstance(driver, TestDriver):
                await driver.connect()

    async def stop_all(self):
        for driver in self.driver_instances.values():
            if isinstance(driver, TestDriver):
                await driver.disconnect()

    @publish_from_arg_async(status=DataFlowStatus.FORWARDED)
    async def send_command(self, data: SendCommandMsg):
        logger.info(f"[COMMAND] Sending command: {data.datapoint_identifier} = {data.value}")
        config = Config.get_instance()
        server_id, _ = data.datapoint_identifier.split("@", 1)

        if not config.validate_value(data.datapoint_identifier, data.value):
            # Value is invalid, send NOK feedback immediately
            feedback = CommandFeedbackMsg(
                command_id=data.command_id,
                datapoint_identifier=data.datapoint_identifier,
                value=data.value,
                feedback="NOK-wrong-value",
                timestamp=datetime.datetime.now(),
            )
            await self.emit_command_feedback(feedback)
            return
        driver = self.driver_instances.get(server_id)
        if driver:
            if driver.is_connected:
                await driver.send_command(data)
            else:
                logger.warning(f"Driver '{server_id}' is not connected. Cannot send command.")
                feedback = CommandFeedbackMsg(
                    command_id=data.command_id,
                    datapoint_identifier=data.datapoint_identifier,
                    value=data.value,
                    feedback="NOK-driver-offline",
                    timestamp=datetime.datetime.now(),
                )
                await self.emit_command_feedback(feedback)

    async def notify_driver_command(self, msg: SendCommandMsg):
        if self._command_listener:
            await self._command_listener.on_driver_command(msg)
