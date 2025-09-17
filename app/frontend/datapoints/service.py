from typing import Any
from app.common.bus.event_bus import EventBus
from app.common.bus.event_types import EventType
from app.common.models.dtos import TagUpdateMsg
from app.frontend.datapoints.controller import DatapointController
from app.frontend.datapoints.model import DatapointModel

class DatapointService:
    def __init__(self, event_bus: EventBus, model: DatapointModel, controller: DatapointController):        
        self._event_bus = event_bus
        event_bus.subscribe(EventType.RAW_TAG_UPDATE, self.on_tag_update)
        self.model = model       
        self._controller = controller
        if controller:
            controller.service = self

    async def update_tag(self, tag_id: str, value: Any, quality: str = "good", timestamp: str = None):
        tag = TagUpdateMsg(datapoint_identifier=tag_id, value=value, quality=quality, timestamp=timestamp)
        await self.on_tag_update(tag)

    async def on_tag_update(self, msg: TagUpdateMsg):    
        print(f"DatapointService received tag update: {msg}")    
        result = self.model.set_tag(msg)
        if result:
            print(f"DatapointService accepted tag update: {msg}")
            await self._event_bus.publish(EventType.TAG_UPDATE, msg)
            print(f"DatapointService published tag update: {msg}")
            if self._controller:
                await self._controller.publish_tag(msg)
            print(f"DatapointService processed tag update: {msg}")
        else:
            print(f"Warning: Received unknown tag_id {msg.datapoint_identifier}")
        print(f"DatapointService finished processing tag update: {msg}")


