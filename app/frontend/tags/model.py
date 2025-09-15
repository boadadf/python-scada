from typing import Dict
from app.common.models.dtos import TagUpdateMsg
from app.common.config.config import Config
from datetime import datetime, timezone

class DatapointModel:
    """
    Stores the current state of all datapoints as TagUpdateMsg objects.
    """
    def __init__(self):
        self._tags: Dict[str, TagUpdateMsg] = {}
        self._allowed_tags = set(Config.get_instance().get_allowed_tags())
        self.initial_load()

    def initial_load(self):
        """
        Initializes all allowed tags with value=None, quality='unknown', and current timestamp.
        """
        now = datetime.now(timezone.utc).isoformat()
        for tag_id in self._allowed_tags:
            self._tags[tag_id] = TagUpdateMsg(
                tag_id=tag_id,
                value=None,
                quality="unknown",
                timestamp=now
            )

    def get_tag(self, tag_id: str) -> TagUpdateMsg:
        return self._tags.get(tag_id)

    def get_all_tags(self) -> Dict[str, TagUpdateMsg]:
        return self._tags.copy()

    def _should_accept_update(self, tag: TagUpdateMsg) -> bool:
        # Condition 1: Tag must be allowed
        if tag.tag_id not in self._allowed_tags:
            return False
        # Condition 2: Ignore older updates or tags that are not in the _tags
        old_tag = self._tags.get(tag.tag_id)
        if old_tag and tag.timestamp is not None and old_tag.timestamp is not None:
            if tag.timestamp < old_tag.timestamp:
                return False
        # Future conditions can be added here
        return True

    def set_tag(self, tag: TagUpdateMsg):
        if not self._should_accept_update(tag):
            return False
        self._tags[tag.tag_id] = tag
        return True
