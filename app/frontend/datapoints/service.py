from typing import Any, Dict
from common.bus.event_bus import EventBus
from common.bus.event_types import TAG_UPDATE
from app.common.models.dtos import TagUpdateMsg
from common.config.config import Config

class DatapointService:
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._tags: Dict[str, TagUpdateMsg] = {}
        self._allowed_tags = set(Config.get_instance().get_allowed_tags())

    def get_tag(self, tag_id: str) -> TagUpdateMsg:
        return self._tags.get(tag_id)

    def get_all_tags(self) -> Dict[str, TagUpdateMsg]:
        return self._tags.copy()

    async def update_tag(self, tag_id: str, value: Any, quality: str = "good", timestamp: str = None):
        if tag_id not in self._allowed_tags:
            print(f"Warning: Ignoring unknown tag_id {tag_id}")
            return
        tag = TagUpdateMsg(tag_id=tag_id, value=value, quality=quality, timestamp=timestamp)
        self._tags[tag_id] = tag
        await self._event_bus.publish(TAG_UPDATE, tag)

    def subscribe_to_eventbus(self):
        async def on_tag_update(msg: TagUpdateMsg):
            tag_id = msg.tag_id
            if tag_id in self._allowed_tags:
                self._tags[tag_id] = msg
            else:
                print(f"Warning: Received unknown tag_id {tag_id}")

        self._event_bus.subscribe(TAG_UPDATE, on_tag_update)

        async def on_initial_state_request(_data):
            await self.publish_initial_state()

        self._event_bus.subscribe("request_initial_state", on_initial_state_request)

    async def publish_initial_state(self):
        for tag in self._tags.values():
            await self._event_bus.publish(TAG_UPDATE, tag)

