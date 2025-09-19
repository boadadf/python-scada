from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import SendCommandMsg
import uuid

class SendCommandAction:
    async def __call__(self, engine, trigger_datapoint_identifier, params):
        datapoint_identifier, value = params
        command_id = str(uuid.uuid4())
        await engine.event_bus.publish(
            EventType.SEND_COMMAND,
            SendCommandMsg(command_id=command_id, datapoint_identifier=datapoint_identifier, value=value)
        )