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

from openscada_lite.modules.rule.actioncommands.action import Action
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import ClientAlertMsg
import uuid

class ClientAlertAction(Action):
    def get_event_data(self, datapoint_identifier, params, track_id, rule_id) -> tuple[ClientAlertMsg, EventType]:
        message, alert_type, command_datapoint, command_value, timeout = params
        return ClientAlertMsg(track_id=track_id, message=message, alert_type=alert_type, command_datapoint=command_datapoint, command_value=command_value, timeout=timeout), EventType.CLIENT_ALERT