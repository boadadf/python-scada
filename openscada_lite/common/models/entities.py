import uuid
import datetime
from datetime import timezone as UTC
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

@dataclass
class Rule:
    rule_id: str
    on_condition: str
    on_actions: List[str] = field(default_factory=list)
    off_condition: Optional[str] = None
    off_actions: List[str] = field(default_factory=list)

@dataclass
class AlarmOccurrence:
    def __init__(self, datapoint_identifier, timestamp=None):
        self.occurrence_id = str(uuid.uuid4())   # unique ID for each occurrence
        self.datapoint_identifier = datapoint_identifier
        self.timestamp = timestamp or datetime.datetime.now(UTC)
        self.active = True
        self.acknowledged = False
        self.finished = False

    def to_dict(self):
        return {
            "occurrence_id": self.occurrence_id,
            "datapoint_identifier": self.datapoint_identifier,
            "timestamp": self.timestamp.isoformat(),
            "active": self.active,
            "acknowledged": self.acknowledged,
            "finished": self.finished,
        }

@dataclass
class DatapointType:
    name: str
    type: str  # e.g. "float", "int", "bool", "enum"
    min: Optional[float] = None
    max: Optional[float] = None
    values: Optional[List[Any]] = None  # For enum types
    default: Optional[Any] = None

@dataclass
class Datapoint:
    name: str
    type: DatapointType
