from app.common.bus.event_types import EventType
from app.common.models.dtos import RaiseAlarmMsg

class RaiseAlarmAction:
    async def __call__(self, engine , tag_id, params):
        await engine.event_bus.publish(
            EventType.RAISE_ALARM,
            RaiseAlarmMsg(datapoint_identifier=tag_id, params=params)
        )