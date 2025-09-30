from openscada_lite.core.rule.actioncommands.action import Action
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import RaiseAlarmMsg

class RaiseAlarmAction(Action):
    def get_event_data(self, datapoint_identifier, params, track_id, rule_id) -> tuple[RaiseAlarmMsg, EventType]:
        return RaiseAlarmMsg(datapoint_identifier=datapoint_identifier, track_id=track_id, rule_id=rule_id), EventType.RAISE_ALARM