from openscada_lite.modules.rule.actioncommands.action import Action
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import ClientAlertMsg
import uuid

class ClientAlertAction(Action):
    def get_event_data(self, datapoint_identifier, params, track_id, rule_id) -> tuple[ClientAlertMsg, EventType]:
        message, alert_type, command_datapoint, command_value, timeout = params
        return ClientAlertMsg(track_id=track_id, message=message, alert_type=alert_type, command_datapoint=command_datapoint, command_value=command_value, timeout=timeout), EventType.CLIENT_ALERT