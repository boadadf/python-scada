from app.common.bus.event_types import LOWER_ALARM
from app.common.models.dtos import LowerAlarmMsg

class LowerAlarmAction:
    async def __call__(self, engine, tag_id, params):
        await engine.event_bus.publish(
            LOWER_ALARM,
            LowerAlarmMsg(tag_id=tag_id, params=params)
        )