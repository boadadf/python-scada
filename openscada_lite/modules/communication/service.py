# -----------------------------------------------------------------------------
# Copyright 2025 Daniel Fernandez Boada
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

# communications_service.py
from typing import override
from openscada_lite.common.tracking.decorators import publish_data_flow_from_arg_async
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.modules.communication.manager.connector_manager import ConnectorManager, CommandListener
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import CommandFeedbackMsg, DriverConnectStatus, DriverConnectCommand, RawTagUpdateMsg, SendCommandMsg, TagUpdateMsg

class CommunicationService(BaseService[[SendCommandMsg, TagUpdateMsg], DriverConnectCommand, DriverConnectStatus], CommandListener):
    def __init__(self, event_bus, model, controller):
        super().__init__(
            event_bus, model, controller,
            [SendCommandMsg, TagUpdateMsg],  # <-- Listen for both
            DriverConnectCommand, DriverConnectStatus
        )
        self.connection_manager = ConnectorManager.get_instance()
        self.connection_manager.register_listener(self)
        self.connection_manager.set_command_listener(self)  # Register as command listener

    @override
    async def async_init(self):
        await self.connection_manager.init_drivers()

    def should_accept_update(self, msg: DriverConnectStatus) -> bool:
        # We accept the update that is coming from the on_driver_connect_status calling super
        return True

    @publish_data_flow_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def handle_bus_message(self, data):
        if isinstance(data, SendCommandMsg):
            # Forward command to connection manager
            await self.connection_manager.send_command(data)
        elif isinstance(data, TagUpdateMsg):
            # Forward TagUpdateMsg to connection manager
            await self.connection_manager.forward_tag_update(data)

    async def on_raw_tag_update(self, msg: RawTagUpdateMsg):
        await self.event_bus.publish(EventType.RAW_TAG_UPDATE, msg)

    async def on_command_feedback(self, msg: CommandFeedbackMsg):
        await self.event_bus.publish(EventType.COMMAND_FEEDBACK, msg)

    async def on_driver_connect_status(self, msg: DriverConnectStatus):
        await self.event_bus.publish(EventType.DRIVER_CONNECT_STATUS, msg)
        await super().handle_bus_message(msg)  # Update internal state if needed        

    async def handle_controller_message(self, data: DriverConnectCommand):
        await self.connection_manager.handle_driver_connect_command(data)

    @publish_data_flow_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def on_driver_command(self, msg: SendCommandMsg):
        await self.event_bus.publish(EventType.SEND_COMMAND, msg)