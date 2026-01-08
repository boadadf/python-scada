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

# datapoint_service.py

from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.tracking.decorators import publish_from_return_sync
from openscada_lite.modules.datapoint.utils import Utils
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import RawTagUpdateMsg, TagUpdateMsg


class DatapointService(BaseService[RawTagUpdateMsg, RawTagUpdateMsg, TagUpdateMsg]):
    def __init__(self, event_bus, model, controller):
        super().__init__(
            event_bus, model, controller, RawTagUpdateMsg, RawTagUpdateMsg, TagUpdateMsg
        )

    async def on_model_accepted_bus_update(self, msg: TagUpdateMsg):
        # Custom logic here
        await self.event_bus.publish(EventType.TAG_UPDATE, msg)

    @publish_from_return_sync(status=DataFlowStatus.CREATED)
    def process_msg(self, msg: RawTagUpdateMsg) -> TagUpdateMsg:
        return TagUpdateMsg(
            datapoint_identifier=msg.datapoint_identifier,
            value=msg.value,
            quality=msg.quality,
            timestamp=msg.timestamp,
            track_id=msg.track_id,
        )

    def should_accept_update(self, tag: RawTagUpdateMsg) -> bool:
        return Utils.is_valid(self.model, tag)
