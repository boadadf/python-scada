# -----------------------------------------------------------------------------
# Copyright 2025 Daniel&Hector Fernandez
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


@dataclass
class AnimationEntry:
    attribute: str
    quality: Dict[str, Any] = field(default_factory=dict)
    expression: Any = None  # str, dict, or alarm mapping {ACTIVE: ..., INACTIVE: ...}
    trigger_type: str = "datapoint"  # 'datapoint' or 'alarm'
    alarm_event: Optional[str] = None  # e.g., 'onAlarmActive', 'onAlarmAck', etc.
    default: Any = None  # value to revert to
    revert_after: float = 0  # seconds after which to revert
    duration: float = 0.5  # default animation duration in seconds


@dataclass
class Animation:
    name: str
    entries: List[AnimationEntry] = field(default_factory=list)
