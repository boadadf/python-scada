import asyncio
from datetime import UTC, datetime
from common.bus.event_bus import EventBus
from common.bus.event_types import ALARM_UPDATE, LOWER_ALARM, RAISE_ALARM, ACK_ALARM
from common.models.entities import AlarmOccurrence
from app.common.models.dtos import RaiseAlarmMsg, LowerAlarmMsg, AckAlarmMsg, AlarmUpdateMsg

class AlarmEngine:
    """
    Tracks alarm occurrences and manages lifecycle:
    active -> inactive -> ack -> finished
    Publishes updates to EventBus for frontend consumption.
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.occurrences = []

        # Subscribe to rule engine events
        event_bus.subscribe(RAISE_ALARM, self.on_alarm_active)
        event_bus.subscribe(LOWER_ALARM, self.on_alarm_inactive)
        event_bus.subscribe(ACK_ALARM, self.on_alarm_ack)

    async def on_alarm_active(self, data: RaiseAlarmMsg):
        """
        Called when a rule triggers an alarm condition.
        Always creates a new AlarmOccurrence.
        """
        occ = AlarmOccurrence(
            tag_id=data.tag_id,
            timestamp=datetime.now(UTC)
        )
        self.occurrences.append(occ)
        await self.publish_update()

    async def on_alarm_inactive(self, data: LowerAlarmMsg):
        """
        Called when a previously active condition is cleared.
        Marks matching active occurrences as inactive.
        """
        for occ in self.occurrences:
            if occ.tag_id == data.tag_id and occ.active and not occ.finished:
                occ.active = False
        await self.publish_update()

    async def on_alarm_ack(self, data: AckAlarmMsg):
        """
        Operator acknowledges an active or inactive alarm.
        """
        for occ in self.occurrences:
            if occ.tag_id == data.tag_id and not occ.finished:
                occ.acknowledged = True
                # Determine if finished
                if not occ.active:
                    occ.finished = True
        await self.publish_update()

    async def publish_update(self):
        """
        Publishes current snapshot of alarms to EventBus.
        """
        snapshot = [occ.to_dict() for occ in self.occurrences if not occ.finished]
        await self.event_bus.publish(ALARM_UPDATE, snapshot)

    def get_active_alarms(self):
        """
        Returns a list of active alarms (for synchronous access if needed)
        """
        return [occ for occ in self.occurrences if occ.active and not occ.finished]

    def get_all_alarms(self):
        """
        Returns all non-finished alarms
        """
        return [occ for occ in self.occurrences if not occ.finished]
