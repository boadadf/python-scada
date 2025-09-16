from app.common.bus.event_types import EventType
from app.common.models.dtos import LowerAlarmMsg

class LowerAlarmAction:
    async def __call__(self, engine, tag_id, params):
        await engine.event_bus.publish(
            EventType.LOWER_ALARM,
            LowerAlarmMsg(datapoint_identifier=tag_id, params=params)
        )