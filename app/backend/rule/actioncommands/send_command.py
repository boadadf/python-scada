from app.common.bus.event_types import EventType
from app.common.models.dtos import SendCommandMsg
import uuid

class SendCommandAction:
    async def __call__(self, engine, tag_id, params):
        target_tag_id, command = params
        command_id = str(uuid.uuid4())
        await engine.event_bus.publish(
            EventType.SEND_COMMAND,
            SendCommandMsg(command_id=command_id, datapoint_identifier=target_tag_id, command=command)
        )