from dataclasses import dataclass, asdict
from typing import Any, Tuple, Optional
import datetime

from openscada_lite.common.bus.event_types import EventType

from abc import ABC, abstractmethod

class DTO(ABC):
    @classmethod
    @abstractmethod
    def get_event_type(cls) -> EventType:
        pass

    @abstractmethod
    def to_dict(self):
        pass

    def _default_to_dict(self):
        d = asdict(self)
        # Convert datetime to isoformat if present
        for k, v in d.items():
            if isinstance(v, datetime.datetime):
                d[k] = v.isoformat()
        return d

@dataclass
class TagUpdateMsg(DTO):
    datapoint_identifier: str
    value: Any
    quality: str = "good"
    timestamp: Optional[str] = None

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.TAG_UPDATE

    def to_dict(self):
        return self._default_to_dict()

@dataclass
class SendCommandMsg(DTO):
    command_id: str
    datapoint_identifier: str
    value: Any

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.SEND_COMMAND

    def to_dict(self):
        return self._default_to_dict()

@dataclass
class CommandFeedbackMsg(DTO):
    command_id: str
    datapoint_identifier: str
    value: str
    feedback: str
    timestamp: Optional[datetime.datetime] = None

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.COMMAND_FEEDBACK

    def to_dict(self):
        return self._default_to_dict()

@dataclass
class RaiseAlarmMsg(DTO):
    datapoint_identifier: str
    params: Tuple[Any, ...] = ()

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.RAISE_ALARM

    def to_dict(self):
        return self._default_to_dict()

@dataclass
class LowerAlarmMsg(DTO):
    datapoint_identifier: str
    params: Tuple[Any, ...] = ()

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.LOWER_ALARM

    def to_dict(self):
        return self._default_to_dict()

@dataclass
class AckAlarmMsg(DTO):
    datapoint_identifier: str
    user: Optional[str] = None

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.ACK_ALARM

    def to_dict(self):
        return self._default_to_dict()

@dataclass
class AlarmUpdateMsg(DTO):
    datapoint_identifier: str
    state: str
    details: Optional[Any] = None

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.ALARM_UPDATE

    def to_dict(self):
        return self._default_to_dict()

@dataclass
class DriverConnectStatus(DTO):
    driver_name: str
    status: str

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.DRIVER_CONNECT_STATUS

    def to_dict(self):
        return self._default_to_dict()

@dataclass
class DriverConnectCommand(DTO):
    driver_name: str
    status: str  # e.g., "connect" or "disconnect"

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.DRIVER_CONNECT_COMMAND

    def to_dict(self):
        return self._default_to_dict()