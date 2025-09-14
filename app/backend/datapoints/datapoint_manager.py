from typing import Any, Dict
from common.bus.event_bus import EventBus
from common.bus.event_types import TAG_UPDATE
from app.common.models.dtos import TagUpdateMsg
from common.config.config import Config

class DatapointEngine:
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._tags: Dict[str, Dict[str, Any]] = {}
        self._allowed_tags = set(Config.get_instance().get_allowed_tags())

    def get_tag(self, tag_id: str) -> Dict[str, Any]:
        return self._tags.get(tag_id)

    def get_all_tags(self) -> Dict[str, Dict[str, Any]]:
        return self._tags.copy()

    async def update_tag(self, tag_id: str, value: Any, quality: str = "good", timestamp: str = None):
        if tag_id not in self._allowed_tags:
            print(f"Warning: Ignoring unknown tag_id {tag_id}")
            return
        self._tags[tag_id] = {"value": value, "quality": quality, "timestamp": timestamp}
        await self._event_bus.publish(
            TAG_UPDATE,
            TagUpdateMsg(tag_id=tag_id, value=value, quality=quality, timestamp=timestamp)
        )

    def subscribe_to_eventbus(self):
        async def on_tag_update(msg: TagUpdateMsg):
            tag_id = msg.tag_id
            if tag_id in self._allowed_tags:
                self._tags[tag_id] = {
                    "value": msg.value,
                    "quality": getattr(msg, "quality", "good"),
                    "timestamp": getattr(msg, "timestamp", None)
                }
            else:
                print(f"Warning: Received unknown tag_id {tag_id}")

        self._event_bus.subscribe(TAG_UPDATE, on_tag_update)

        # Special event to request initial state
        async def on_initial_state_request(_data):
            await self.publish_initial_state()

        self._event_bus.subscribe("request_initial_state", on_initial_state_request)

    async def publish_initial_state(self):
        for tag_id, info in self._tags.items():
            await self._event_bus.publish(
                TAG_UPDATE,
                TagUpdateMsg(
                    tag_id=tag_id,
                    value=info["value"],
                    quality=info.get("quality", "good"),
                    timestamp=info.get("timestamp")
                )
            )

