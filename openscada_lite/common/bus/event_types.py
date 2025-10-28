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

from enum import Enum, unique

"""
Defines all event types used in the EventBus.
"""
@unique
class EventType(Enum):
    RAW_TAG_UPDATE = "raw_tag_update"
    TAG_UPDATE = "tag_update"
    SEND_COMMAND = "send_command"
    COMMAND_FEEDBACK = "command_feedback"
    RAISE_ALARM = "raise_alarm"
    LOWER_ALARM = "lower_alarm"
    ACK_ALARM = "ack_alarm"
    ALARM_UPDATE = "alarm_update"
    DRIVER_CONNECT_COMMAND = "driver_connect"
    DRIVER_CONNECT_STATUS = "driver_connect_status"
    FLOW_EVENT = "flow_event"
    ANIMATION_EVENT = "animation_event"
    ANIMATION_REQUEST = "animation_request"
    CLIENT_ALERT = "client_alert"
    CLIENT_ALERT_FEEDBACK = "client_alert_feedback"