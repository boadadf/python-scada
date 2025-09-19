from dataclasses import dataclass
from typing import Any, Tuple, Optional
import datetime

@dataclass
class TagUpdateMsg:
    datapoint_identifier: str
    value: Any
    quality: str = "good"
    timestamp: Optional[str] = None
    def to_dict(self):
        d = self.__dict__.copy()
        ts = d.get("timestamp")
        if ts is not None and isinstance(ts, datetime.datetime):
            d["timestamp"] = ts.isoformat()
        return d
    
@dataclass
class SendCommandMsg:
    command_id: str
    datapoint_identifier: str
    value: Any

@dataclass
class CommandFeedbackMsg:
    command_id: str
    datapoint_identifier: str
    value: str
    feedback: str
    timestamp: Optional[datetime.datetime] = None
 
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
