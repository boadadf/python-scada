import asyncio
from datetime import UTC, datetime
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.entities import AlarmOccurrence
from openscada_lite.common.models.dtos import RaiseAlarmMsg, LowerAlarmMsg, AckAlarmMsg, AlarmUpdateMsg

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
        event_bus.subscribe(EventType.RAISE_ALARM, self.on_alarm_active)
        event_bus.subscribe(EventType.LOWER_ALARM, self.on_alarm_inactive)
        event_bus.subscribe(EventType.ACK_ALARM, self.on_alarm_ack)

    async def on_alarm_active(self, data: RaiseAlarmMsg):
        """
        Called when a rule triggers an alarm condition.
        Always creates a new AlarmOccurrence.
        """
        occ = AlarmOccurrence(
            datapoint_identifier=data.datapoint_identifier,
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
            if occ.datapoint_identifier == data.datapoint_identifier and occ.active and not occ.finished:
                occ.active = False
        await self.publish_update()

    async def on_alarm_ack(self, data: AckAlarmMsg):
        """
        Operator acknowledges an active or inactive alarm.
        """
        for occ in self.occurrences:
            if occ.datapoint_identifier == data.datapoint_identifier and not occ.finished:
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
        await self.event_bus.publish(EventType.ALARM_UPDATE, snapshot)

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
