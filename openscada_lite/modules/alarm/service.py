from typing import Union, override
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
        if isinstance(msg, (LowerAlarmMsg)):
            msg_lower: LowerAlarmMsg = msg
            alarm = Utils.get_latest_alarm(self.model, msg_lower.get_id())
            if (alarm and alarm.deactivation_time is None):
                return True
        elif isinstance(msg, (RaiseAlarmMsg)):
            return True            
        # Other cases, the alarm cannot be accepted
        return False

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
        print("DatapointService.on_model_accepted_bus_update CALLED")
        alarm = self.model.get(data.alarm_occurrence_id)
        alarm.acknowledge_time = data.timestamp
        self.model.update(alarm)
        await self.event_bus.publish(alarm.get_event_type(), alarm)
        
    async def on_model_accepted_bus_update(self, msg: AlarmUpdateMsg):
        await self.event_bus.publish(EventType.ALARM_UPDATE, msg)