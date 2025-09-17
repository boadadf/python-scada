from dataclasses import dataclass
from typing import Any, Tuple, Optional

@dataclass
class TagUpdateMsg:
    datapoint_identifier: str
    value: Any
    quality: str = "good"
    timestamp: Optional[str] = None
    def to_dict(self):
        d = self.__dict__.copy()
        if "timestamp" in d and d["timestamp"] is not None:
            d["timestamp"] = d["timestamp"].isoformat()
        return d
    
@dataclass
class SendCommandMsg:
    command_id: str
    datapoint_identifier: str
    command: Any

@dataclass
class CommandFeedbackMsg:
    command_id: str
    status: str
    datapoint_identifier: str
 
@dataclass
class RaiseAlarmMsg:
    datapoint_identifier: str
    params: Tuple[Any, ...] = ()

@dataclass
class LowerAlarmMsg:
    datapoint_identifier: str
    params: Tuple[Any, ...] = ()

@dataclass
class AckAlarmMsg:
    datapoint_identifier: str
    user: Optional[str] = None

@dataclass
class AlarmUpdateMsg:
    datapoint_identifier: str
    state: str
    details: Optional[Any] = None

@dataclass
class CommunicationStatusMsg:
    server_name: str
    status: str
