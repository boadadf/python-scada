# datapoint_service.py
from typing import override
from openscada_lite.modules.datapoint.utils import Utils
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import RawTagUpdateMsg, TagUpdateMsg

class DatapointService(BaseService[RawTagUpdateMsg, RawTagUpdateMsg, TagUpdateMsg]):
    def __init__(self, event_bus, model, controller):
        super().__init__(event_bus, model, controller, RawTagUpdateMsg, RawTagUpdateMsg, TagUpdateMsg)

    @override
    async def on_model_accepted_bus_update(self, msg: TagUpdateMsg):
        # Custom logic here
        await self.event_bus.publish(EventType.TAG_UPDATE, msg)

    @override    
    def process_msg(self, msg: RawTagUpdateMsg) -> TagUpdateMsg:
        return TagUpdateMsg(datapoint_identifier=msg.datapoint_identifier, value=msg.value, quality=msg.quality, timestamp=msg.timestamp)
    
    @override
    def should_accept_update(self, tag: RawTagUpdateMsg) -> bool:
        return Utils.is_valid(self.model, tag)