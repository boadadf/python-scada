from app.common.bus.event_types import RAISE_ALARM
from app.common.models.dtos import RaiseAlarmMsg

class RaiseAlarmAction:
    async def __call__(self, engine, tag_id, params):
        await engine.event_bus.publish(
            RAISE_ALARM,
            RaiseAlarmMsg(tag_id=tag_id, params=params)
        )