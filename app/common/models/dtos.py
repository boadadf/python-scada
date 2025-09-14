from dataclasses import dataclass
from typing import Any, Tuple, Optional

@dataclass
class TagUpdateMsg:
    tag_id: str
    value: Any
    quality: str = "good"
    timestamp: Optional[str] = None

@dataclass
class SendCommandMsg:
    command_id: str
    tag_id: str
    command: Any

@dataclass
class CommandFeedbackMsg:
    command_id: str
    status: str
    tag_id: str
 
@dataclass
class RaiseAlarmMsg:
    tag_id: str
    params: Tuple[Any, ...] = ()

@dataclass
class LowerAlarmMsg:
    tag_id: str
    params: Tuple[Any, ...] = ()

@dataclass
class AckAlarmMsg:
    tag_id: str
    user: Optional[str] = None

@dataclass
class AlarmUpdateMsg:
    tag_id: str
    state: str
    details: Optional[Any] = None