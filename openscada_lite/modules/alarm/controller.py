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

from typing import Union
from openscada_lite.modules.alarm.model import AlarmModel
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import AckAlarmMsg, AlarmUpdateMsg, StatusDTO

class AlarmController(BaseController[AlarmUpdateMsg, AckAlarmMsg]):
    def __init__(self, model: AlarmModel, socketio, base_event: str, flask_app=None):
        super().__init__(model, socketio, AlarmUpdateMsg, AckAlarmMsg, base_event=base_event, flask_app=flask_app)
        self.model: AlarmModel = model
    def validate_request_data(self, data: AckAlarmMsg) -> Union[AckAlarmMsg, StatusDTO]:
        # Validation: alarm must exist, not finished, not already acknowledged
        alarm = self.model.get(data.alarm_occurrence_id)
        if not alarm or alarm.isFinished() or alarm.acknowledge_time is not None:
            return StatusDTO("error", "Invalid alarm state")
        return data
