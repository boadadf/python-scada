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

import copy
from typing import Union, override
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.tracking.decorators import publish_data_flow_from_return_sync
from openscada_lite.modules.alarm.controller import AlarmController
from openscada_lite.modules.alarm.model import AlarmModel
from openscada_lite.modules.alarm.utils import Utils
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import AckAlarmMsg, RaiseAlarmMsg, LowerAlarmMsg, AlarmUpdateMsg

class AlarmService(BaseService[Union[RaiseAlarmMsg, LowerAlarmMsg], AckAlarmMsg, AlarmUpdateMsg]):
    def __init__(self, event_bus, model: AlarmModel, controller: AlarmController):
        super().__init__(event_bus, model, controller, [RaiseAlarmMsg, LowerAlarmMsg], AckAlarmMsg, AlarmUpdateMsg)
        self.model = model
        self.event_bus = event_bus
        
    @override
    def should_accept_update(self, msg) -> bool:
        if isinstance(msg, LowerAlarmMsg):
            msg_lower: LowerAlarmMsg = msg
            alarm = Utils.get_latest_alarm(self.model, msg_lower.get_id())
            if alarm and alarm.deactivation_time is None:
                return True
        elif isinstance(msg, RaiseAlarmMsg):
            msg_raise: RaiseAlarmMsg = msg
            alarm = Utils.get_latest_alarm(self.model, msg_raise.get_id())
            # Accept only if last alarm is deactivated (deactivation_time is not None)
            if alarm is None or alarm.deactivation_time is not None:
                return True
        # Other cases, the alarm cannot be accepted
        return False

    @publish_data_flow_from_return_sync(status=DataFlowStatus.CREATED)
    @override
    def process_msg(self, msg) -> AlarmUpdateMsg:
        #Raise can one mean reset deactivation and acknowledge to None
        if isinstance(msg, RaiseAlarmMsg):
            msg_raise: RaiseAlarmMsg = msg
            return AlarmUpdateMsg(
                datapoint_identifier=msg_raise.datapoint_identifier,
                activation_time=msg_raise.timestamp,
                deactivation_time=None,
                acknowledge_time=None,
                rule_id=msg_raise.rule_id
            )
        #Lower can only set deactivation time
        elif isinstance(msg, LowerAlarmMsg):
            msg_lower: LowerAlarmMsg = msg
            existing_alarm = Utils.get_latest_alarm(self.model, msg_lower.get_id())
            if existing_alarm:
                existing_alarm.deactivation_time = msg_lower.timestamp
                return existing_alarm
        raise ValueError("Unsupported message type for processing")
    
    @override
    async def handle_controller_message(self, data: AckAlarmMsg):
        alarm = self.model.get(data.alarm_occurrence_id)
        alarm.acknowledge_time = data.timestamp
        self.model.update(alarm)
        await self.event_bus.publish(alarm.get_event_type(), alarm)
        if self.controller:
            self.controller.publish(alarm)

    #Publish alarm updates to the bus in case another service wants to listen
    @override
    async def on_model_accepted_bus_update(self, msg: AlarmUpdateMsg):
        updated = copy.deepcopy(msg)
        await self.event_bus.publish(EventType.ALARM_UPDATE, updated)