import pytest
import asyncio
from datetime import datetime

from openscada_lite.backend.alarm.alarm_engine import AlarmEngine
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import RaiseAlarmMsg, LowerAlarmMsg, AckAlarmMsg, AlarmUpdateMsg

@pytest.mark.asyncio
async def test_alarm_active_creation():
    bus = EventBus()
    alarm_engine = AlarmEngine(bus)

    updates = []
    async def capture(data):
        updates.append(data)
    bus.subscribe(EventType.ALARM_UPDATE, capture)

    # Trigger an active alarm
    await bus.publish(EventType.RAISE_ALARM, RaiseAlarmMsg(datapoint_identifier="tag1"))
    await asyncio.sleep(0.01)

    # Check occurrence created
    assert len(updates) == 1
    assert updates[0][0]["datapoint_identifier"] == "tag1"
    assert updates[0][0]["active"] is True
    assert updates[0][0]["acknowledged"] is False
    assert updates[0][0]["finished"] is False


@pytest.mark.asyncio
async def test_alarm_inactive_transition():
    bus = EventBus()
    alarm_engine = AlarmEngine(bus)

    updates = []
    async def capture(data):
        updates.append(data)
    bus.subscribe(EventType.ALARM_UPDATE, capture)

    # Active alarm
    await bus.publish(EventType.RAISE_ALARM, RaiseAlarmMsg(datapoint_identifier="tag1"))
    await asyncio.sleep(0.01)

    # Inactive transition
    await bus.publish(EventType.LOWER_ALARM, LowerAlarmMsg(datapoint_identifier="tag1"))
    await asyncio.sleep(0.01)

    # Check inactive
    occ = updates[-1][0]
    assert occ["active"] is False
    assert occ["acknowledged"] is False
    assert occ["finished"] is False


@pytest.mark.asyncio
async def test_alarm_acknowledge_active():
    bus = EventBus()
    alarm_engine = AlarmEngine(bus)

    updates = []
    async def capture(data):
        updates.append(data)
    bus.subscribe(EventType.ALARM_UPDATE, capture)

    # Active alarm
    await bus.publish(EventType.RAISE_ALARM, RaiseAlarmMsg(datapoint_identifier="tag1"))
    await asyncio.sleep(0.01)

    # Acknowledge while active
    await bus.publish(EventType.ACK_ALARM, AckAlarmMsg(datapoint_identifier="tag1"))
    await asyncio.sleep(0.01)

    occ = updates[-1][0]
    assert occ["active"] is True
    assert occ["acknowledged"] is True
    assert occ["finished"] is False


@pytest.mark.asyncio
async def test_alarm_acknowledge_inactive_finishes():
    bus = EventBus()
    alarm_engine = AlarmEngine(bus)

    updates = []
    async def capture(data):
        updates.append(data)
    bus.subscribe(EventType.ALARM_UPDATE, capture)

    # Active -> Inactive
    await bus.publish(EventType.RAISE_ALARM, RaiseAlarmMsg(datapoint_identifier="tag1"))
    await asyncio.sleep(0.01)
    await bus.publish(EventType.LOWER_ALARM, LowerAlarmMsg(datapoint_identifier="tag1"))
    await asyncio.sleep(0.01)

    # Ack after inactive -> finished
    await bus.publish(EventType.ACK_ALARM, AckAlarmMsg(datapoint_identifier="tag1"))
    await asyncio.sleep(0.01)

    # After finishing, alarm_update should exclude finished alarms
    assert len(updates[-1]) == 0

@pytest.mark.asyncio
async def test_recursive_alarms_full_updates():
    bus = EventBus()
    alarm_engine = AlarmEngine(bus)

    updates = []

    async def capture(data):
        # Make a copy of the snapshot at this moment
        updates.append([dict(occ) for occ in data])

    bus.subscribe(EventType.ALARM_UPDATE, capture)

    # First occurrence active
    await bus.publish(EventType.RAISE_ALARM, RaiseAlarmMsg(datapoint_identifier="door"))
    await asyncio.sleep(0.01)

    # First occurrence inactive
    await bus.publish(EventType.LOWER_ALARM, LowerAlarmMsg(datapoint_identifier="door"))
    await asyncio.sleep(0.01)

    # Second occurrence active
    await bus.publish(EventType.RAISE_ALARM, RaiseAlarmMsg(datapoint_identifier="door"))
    await asyncio.sleep(0.01)

    # Check all updates
    assert len(updates) == 3

    # First snapshot → occurrence #1 active
    assert updates[0][0]["active"] is True

    # Second snapshot → occurrence #1 inactive
    assert updates[1][0]["active"] is False

    # Third snapshot → occurrence #1 inactive, occurrence #2 active
    assert len(updates[2]) == 2
    inactive_occ = [a for a in updates[2] if a["active"] is False]
    active_occ = [a for a in updates[2] if a["active"] is True]
    assert len(inactive_occ) == 1
    assert len(active_occ) == 1

@pytest.mark.asyncio
async def test_alarm_active_inactive_ack():
    bus = EventBus()
    alarm_engine = AlarmEngine(bus)

    updates = []

    async def capture(data):
        updates.append([dict(occ) for occ in data])

    bus.subscribe(EventType.ALARM_UPDATE, capture)

    # Active alarm
    await bus.publish(EventType.RAISE_ALARM, RaiseAlarmMsg(datapoint_identifier="rule1"))
    await asyncio.sleep(0.01)

    occ_id = updates[0][0]["occurrence_id"]

    # Inactive
    await bus.publish(EventType.LOWER_ALARM, LowerAlarmMsg(datapoint_identifier="rule1"))
    await asyncio.sleep(0.01)

    assert updates[1][0]["occurrence_id"] == occ_id
    assert updates[1][0]["active"] is False

    # Ack → finishes since inactive
    await bus.publish(EventType.ACK_ALARM, AckAlarmMsg(datapoint_identifier="rule1"))
    await asyncio.sleep(0.01)

    # Finished → should not appear in last update
    assert len(updates[-1]) == 0


@pytest.mark.asyncio
async def test_recursive_alarms():
    bus = EventBus()
    alarm_engine = AlarmEngine(bus)

    updates = []

    async def capture(data):
        updates.append([dict(occ) for occ in data])

    bus.subscribe(EventType.ALARM_UPDATE, capture)

    # First occurrence active
    await bus.publish(EventType.RAISE_ALARM, RaiseAlarmMsg(datapoint_identifier="door"))
    await asyncio.sleep(0.01)
    occ1 = updates[-1][0]["occurrence_id"]

    # First occurrence inactive
    await bus.publish(EventType.LOWER_ALARM, LowerAlarmMsg(datapoint_identifier="door"))
    await asyncio.sleep(0.01)

    # Second occurrence active
    await bus.publish(EventType.RAISE_ALARM, RaiseAlarmMsg(datapoint_identifier="door"))
    await asyncio.sleep(0.01)
    occ2 = [occ for occ in updates[-1] if occ["active"]][0]["occurrence_id"]

    # Check snapshots
    assert len(updates) == 3
    # First snapshot → first occurrence active
    assert updates[0][0]["occurrence_id"] == occ1 and updates[0][0]["active"]
    # Second snapshot → first occurrence inactive
    assert updates[1][0]["occurrence_id"] == occ1 and not updates[1][0]["active"]
    # Third snapshot → first occurrence inactive, second occurrence active
    active_occ = [a for a in updates[2] if a["active"]]
    inactive_occ = [a for a in updates[2] if not a["active"]]
    assert len(active_occ) == 1 and active_occ[0]["occurrence_id"] == occ2
    assert len(inactive_occ) == 1 and inactive_occ[0]["occurrence_id"] == occ1
