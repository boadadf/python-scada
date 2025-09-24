from typing import Union, override
from openscada_lite.modules.alarm.model import AlarmModel
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import AckAlarmMsg, AlarmUpdateMsg, CommandFeedbackMsg, StatusDTO

class AlarmController(BaseController[AlarmUpdateMsg, AckAlarmMsg]):
    def __init__(self, model: AlarmModel, socketio):
        super().__init__(model, socketio, AlarmUpdateMsg, AckAlarmMsg, base_event="alarm")
        self.model: AlarmModel = model

    @override
    def validate_request_data(self, data: AckAlarmMsg) -> Union[AckAlarmMsg, StatusDTO]:
        # Validation: alarm must exist, not finished, not already acknowledged
        alarm = self.model.get(data.alarm_occurrence_id)
        if not alarm or alarm.isFinished() or alarm.acknowledge_time is not None:
            return StatusDTO("error", "Invalid alarm state")
        return alarm
