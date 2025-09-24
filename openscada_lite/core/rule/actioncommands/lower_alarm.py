from openscada_lite.core.rule.actioncommands.action import Action
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import DTO, LowerAlarmMsg

class LowerAlarmAction(Action):
    def get_event_data(self, datapoint_identifier, params, track_id) -> tuple[EventType, DTO]:
        return EventType.LOWER_ALARM, LowerAlarmMsg(datapoint_identifier=datapoint_identifier, track_id=track_id)