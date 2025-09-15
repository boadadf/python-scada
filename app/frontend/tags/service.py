from typing import Any
from app.common.bus.event_bus import EventBus
from app.common.bus.event_types import RAW_TAG_UPDATE, TAG_UPDATE
from app.common.models.dtos import TagUpdateMsg
from app.frontend.tags.controller import DatapointController
from app.frontend.tags.model import DatapointModel

class DatapointService:
    def __init__(self, event_bus: EventBus, model: DatapointModel, controller: DatapointController):        
        self._event_bus = event_bus
        event_bus.subscribe(RAW_TAG_UPDATE, self.on_tag_update)
        self.model = model       
        self._controller = controller

    async def update_tag(self, tag_id: str, value: Any, quality: str = "good", timestamp: str = None):
        tag = TagUpdateMsg(tag_id=tag_id, value=value, quality=quality, timestamp=timestamp)
        await self.on_tag_update(tag)

    async def on_tag_update(self, msg: TagUpdateMsg):        
        result = self.model.set_tag(msg)
        if result:
            await self._event_bus.publish(TAG_UPDATE, msg)
            if self._controller:
                self._controller.publish_tag(msg)
        else:
            print(f"Warning: Received unknown tag_id {msg.tag_id}")


