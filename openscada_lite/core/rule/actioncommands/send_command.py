from openscada_lite.core.rule.actioncommands.action import Action
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import SendCommandMsg
import uuid

class SendCommandAction(Action):
    def get_event_data(self, datapoint_identifier, params, track_id, rule_id) -> tuple[SendCommandMsg, EventType]:
        datapoint_identifier, value = params
        command_id = str(uuid.uuid4())
        return SendCommandMsg(command_id=command_id, datapoint_identifier=datapoint_identifier, value=value, track_id=track_id), EventType.SEND_COMMAND