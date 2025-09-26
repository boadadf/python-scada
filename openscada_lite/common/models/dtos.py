from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Tuple, Optional
import datetime
import uuid

from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.bus.event_types import EventType

from abc import ABC, abstractmethod

@dataclass(kw_only=True)
class DTO(ABC):
    """Base class for Data Transfer Objects (DTOs) used in the system."""
    track_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    #The payload for each DTO
    def get_track_payload(self) -> str:
        """Return a serializable representation for tracking."""
        return ""

    @classmethod 
    @abstractmethod
    def get_event_type(cls) -> EventType:
        pass

    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def to_dict(self):
        pass

    def _default_to_dict(self):
        d = asdict(self)
        return make_json_serializable(d)

def make_json_serializable(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    else:
        return obj

@dataclass
class TagUpdateMsg(DTO):
    datapoint_identifier: str
    value: Any
    quality: str = "good"
    timestamp: Optional[datetime.datetime] = None

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.TAG_UPDATE

    def to_dict(self):
        return self._default_to_dict()

    def get_id(self) -> str:
        return self.datapoint_identifier

    def get_track_payload(self):
        return {
            "datapoint_identifier": self.datapoint_identifier,
            "value": self.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

@dataclass
class RawTagUpdateMsg(DTO):
    datapoint_identifier: str
    value: Any
    quality: str = "good"
    timestamp: Optional[datetime.datetime] = None

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.RAW_TAG_UPDATE

    def to_dict(self):
        return self._default_to_dict()

    def get_id(self) -> str:
        return self.datapoint_identifier

    def get_track_payload(self):
        return {
            "datapoint_identifier": self.datapoint_identifier,
            "value": self.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

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

    def get_id(self) -> str:
        return self.datapoint_identifier

    def get_track_payload(self):
        return {
            "command_id": self.command_id,
            "datapoint_identifier": self.datapoint_identifier,
            "value": self.value
        }

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

    def get_id(self) -> str:
        return self.datapoint_identifier

    def get_track_payload(self):
        return {
            "command_id": str(self.command_id), 
            "datapoint_identifier": self.datapoint_identifier,
            "value": self.value,
            "feedback": self.feedback,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
    }

@dataclass
class RaiseAlarmMsg(DTO):
    datapoint_identifier: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.RAISE_ALARM

    def to_dict(self):
        return self._default_to_dict()

    def get_id(self) -> str:
        return self.datapoint_identifier

    def get_track_payload(self):
        return {
            "datapoint_identifier": self.datapoint_identifier,
            "timestamp": self.timestamp.isoformat(),
        }

@dataclass
class LowerAlarmMsg(DTO):
    datapoint_identifier: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.LOWER_ALARM

    def to_dict(self):
        return self._default_to_dict()

    def get_id(self) -> str:
        return self.datapoint_identifier

    def get_track_payload(self):
        return {
            "datapoint_identifier": self.datapoint_identifier,
            "timestamp": self.timestamp.isoformat(),
        }

@dataclass
class AckAlarmMsg(DTO):
    alarm_occurrence_id: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.ACK_ALARM

    def to_dict(self):
        return self._default_to_dict()

    def get_id(self) -> str:
        return self.alarm_occurrence_id

    def get_track_payload(self):
        return {
            "alarm_occurrence_id": self.alarm_occurrence_id,
            "timestamp": self.timestamp.isoformat(),
        }

@dataclass
class AlarmUpdateMsg(DTO):
    datapoint_identifier: str
    activation_time: datetime.datetime
    deactivation_time: Optional[datetime.datetime] = None
    acknowledge_time: Optional[datetime.datetime] = None

    @property
    def alarm_occurrence_id(self) -> str:
        return self.get_id()

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.ALARM_UPDATE

    def to_dict(self):
        return self._default_to_dict()

    def get_id(self) -> str:
        return f'{self.datapoint_identifier}@{self.activation_time.isoformat()}'
    
    def isFinished(self) -> bool:
        return self.deactivation_time is not None \
            and self.acknowledge_time is not None \
            and self.activation_time is not None

    def get_track_payload(self):
        return {
            "datapoint_identifier": self.datapoint_identifier,
            "activation_time": self.activation_time.isoformat(),
            "deactivation_time": self.deactivation_time.isoformat() if self.deactivation_time else None,
            "acknowledge_time": self.acknowledge_time.isoformat() if self.acknowledge_time else None,
        }

@dataclass
class DriverConnectStatus(DTO):
    driver_name: str
    status: str

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.DRIVER_CONNECT_STATUS

    def to_dict(self):
        return self._default_to_dict()

    def get_id(self) -> str:
        return self.driver_name
    
    def get_track_payload(self):
        return {
            "driver_name": self.driver_name,
            "status": self.status
        }

@dataclass
class DriverConnectCommand(DTO):
    driver_name: str
    status: str  # e.g., "connect" or "disconnect"

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.DRIVER_CONNECT_COMMAND

    def to_dict(self):
        return self._default_to_dict()
    
    def get_id(self) -> str:
        return self.driver_name

    def get_track_payload(self):
        return {
            "driver_name": self.driver_name,
            "status": self.status
        }

@dataclass
class StatusDTO():
    status: str
    reason: str

    def to_dict(self):
        return {
            "status": self.status,
            "reason": self.reason
        }

    def get_id(self) -> str:
        return self.status
    
@dataclass
class DataFlowEventMsg(DTO):
    event_type: str
    source: str
    status: DataFlowStatus
    timestamp: datetime.datetime
    payload: dict

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.FLOW_EVENT

    def to_dict(self):
        return self._default_to_dict()
    
    def get_id(self) -> str:
        return f'{self.track_id}@{self.source}@{self.event_type}'

    def get_track_payload(self):
        print(f"DataFlowEventMsg payload: {self.to_dict()}")
        return {
            "track_id": str(self.track_id),
            "event_type": self.event_type,
            "source": self.source,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload
        }