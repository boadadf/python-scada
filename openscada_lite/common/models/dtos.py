# -----------------------------------------------------------------------------
# Copyright 2025 Daniel Fernandez Boada
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Optional, Union
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
    test: bool = False

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
    rule_id: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    
    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.RAISE_ALARM

    def to_dict(self):
        return self._default_to_dict()

    def get_id(self) -> str:
        return self.rule_id

    def get_track_payload(self):
        return {
            "datapoint_identifier": self.datapoint_identifier,
            "timestamp": self.timestamp.isoformat(),
        }

@dataclass
class LowerAlarmMsg(DTO):
    datapoint_identifier: str
    rule_id: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)    

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.LOWER_ALARM

    def to_dict(self):
        return self._default_to_dict()

    def get_id(self) -> str:
        return self.rule_id

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
    rule_id: Optional[str] = None
    test: bool = False

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
        return {
            "track_id": str(self.track_id),
            "event_type": self.event_type,
            "source": self.source,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload
        }

@dataclass
class AnimationUpdateMsg(DTO):
    svg_name: str
    element_id: str
    animation_type: str
    value: float
    config: dict
    timestamp: Optional[datetime.datetime] = None
    test: bool = False
    
    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.ANIMATION_EVENT

    def to_dict(self):
        return self._default_to_dict()
    
    def get_id(self) -> str:
        return f"{self.svg_name}:{self.element_id}"

    def get_track_payload(self):
        return {
            "element_id": self.element_id,
            "animation": self.animation_type,
            "value": self.value,
            "svg_name": self.svg_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

@dataclass
class AnimationUpdateRequestMsg(DTO):
    datapoint_identifier: str
    quality: str
    value: float = 0.09
    alarm_status: str | None = None  # <-- NEW
    
    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.ANIMATION_REQUEST

    def to_dict(self):
        return self._default_to_dict()
    
    def get_id(self) -> str:
        return f"{self.datapoint_identifier}:{self.quality}:{self.value}"

    def get_track_payload(self):
        return {
            "datapoint_identifier": self.datapoint_identifier,
            "quality": self.quality,
            "value": self.value
        }                

    def to_test_update_msg(self) -> Union[AlarmUpdateMsg, TagUpdateMsg]:
        if self.alarm_status:
            """Generate a simulated AlarmUpdateMsg for testing animations."""
            now = datetime.datetime.now()
            status = (self.alarm_status or "UNKNOWN").upper()

            activation_time = now if status in ["ACTIVE", "ACK", "INACTIVE", "FINISHED"] else None
            acknowledge_time = now if status in ["ACK", "INACTIVE", "FINISHED"] else None
            deactivation_time = now if status in ["INACTIVE", "FINISHED"] else None

            return AlarmUpdateMsg(
                datapoint_identifier=self.datapoint_identifier,
                activation_time=activation_time,
                acknowledge_time=acknowledge_time,
                deactivation_time=deactivation_time,
                rule_id="manual_test_alarm",
                test=True,
            )
        else:
            return TagUpdateMsg(
                datapoint_identifier=self.datapoint_identifier,
                value=self.value,
                quality=self.quality,
                test=True
            )


@dataclass
class ClientAlertMsg(DTO):    
    message: str
    alert_type: str
    show: bool = True  # True to show, False to hide
    command_datapoint: Optional[str] = None
    command_value: Optional[str] = None
    timeout: Optional[int] = None  # in seconds

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.CLIENT_ALERT

    def to_dict(self):
        return self._default_to_dict()

    def get_id(self) -> str:
        return self.track_id

    def get_track_payload(self):
        return {
            "message": self.message,
            "command_datapoint": self.command_datapoint,
            "command_value": self.command_value
        }
    
@dataclass
class ClientAlertFeedbackMsg(DTO):
    #track_id is inherited from DTO
    feedback: str  # e.g., "confirm" "cancel"

    @classmethod
    def get_event_type(cls) -> EventType:
        return EventType.CLIENT_ALERT_FEEDBACK

    def to_dict(self):
        return self._default_to_dict()

    def get_id(self) -> str:
        return self.track_id

    def get_track_payload(self):
        return {
            "feedback": self.feedback
        }    