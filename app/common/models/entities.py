import uuid
import datetime
from datetime import timezone as UTC
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Rule:
    rule_id: str
    on_condition: str
    on_actions: List[str] = field(default_factory=list)
    off_condition: Optional[str] = None
    off_actions: List[str] = field(default_factory=list)

@dataclass
class AlarmOccurrence:
    def __init__(self, tag_id, timestamp=None):
        self.occurrence_id = str(uuid.uuid4())   # unique ID for each occurrence
        self.tag_id = tag_id
        self.timestamp = timestamp or datetime.datetime.now(UTC)
        self.active = True
        self.acknowledged = False
        self.finished = False

    def to_dict(self):
        return {
            "occurrence_id": self.occurrence_id,
            "tag_id": self.tag_id,
            "timestamp": self.timestamp.isoformat(),
            "active": self.active,
            "acknowledged": self.acknowledged,
            "finished": self.finished,
        }
