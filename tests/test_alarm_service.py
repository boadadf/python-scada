import pytest
import asyncio
from datetime import datetime

from openscada_lite.modules.alarm.model import AlarmModel
from openscada_lite.modules.alarm.service import AlarmService
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import (
    RaiseAlarmMsg,
    LowerAlarmMsg,
    AckAlarmMsg,
    AlarmUpdateMsg,
)


# Reset the bus for each test
@pytest.fixture(autouse=True)
def reset_event_bus(monkeypatch):
    # Reset the singleton before each test
    monkeypatch.setattr(EventBus, "_instance", None)


@pytest.mark.asyncio
async def test_alarm_active_creation():
    bus = EventBus.get_instance()
    model = AlarmModel()
    AlarmService(bus, model, controller=None)

    updates = []

    async def capture(data):
        updates.append(data)

    bus.subscribe(EventType.ALARM_UPDATE, capture)

    await bus.publish(
        EventType.RAISE_ALARM,
        RaiseAlarmMsg(datapoint_identifier="tag1", timestamp=datetime.now(), rule_id="rule1"),
    )
    await asyncio.sleep(0.01)

    assert len(updates) == 1
    alarm_update: AlarmUpdateMsg = updates[0]
    assert alarm_update.datapoint_identifier == "tag1"
    assert alarm_update.activation_time is not None
    assert alarm_update.isFinished() is False


@pytest.mark.asyncio
async def test_alarm_inactive_transition():
    bus = EventBus.get_instance()
    model = AlarmModel()
    AlarmService(bus, model, controller=None)

    updates = []

    async def capture(data):
        updates.append(data)

    bus.subscribe(EventType.ALARM_UPDATE, capture)

    await bus.publish(
        EventType.RAISE_ALARM,
        RaiseAlarmMsg(datapoint_identifier="tag1", timestamp=datetime.now(), rule_id="rule1"),
    )
    await asyncio.sleep(0.01)
    await bus.publish(
        EventType.LOWER_ALARM,
        LowerAlarmMsg(datapoint_identifier="tag1", rule_id="rule1"),
    )
    await asyncio.sleep(0.01)

    assert len(updates) == 2
    alarm_update: AlarmUpdateMsg = updates[1]
    assert alarm_update.datapoint_identifier == "tag1"
    assert alarm_update.activation_time is not None
    assert alarm_update.deactivation_time is not None
    assert alarm_update.isFinished() is False


@pytest.mark.asyncio
async def test_alarm_acknowledge_active():
    bus = EventBus.get_instance()
    model = AlarmModel()
    service = AlarmService(bus, model, controller=None)

    updates = []

    async def capture(data):
        updates.append(data)

    bus.subscribe(EventType.ALARM_UPDATE, capture)

    test_alarm = RaiseAlarmMsg(
        datapoint_identifier="tag1", timestamp=datetime.now(), rule_id="rule1"
    )
    await bus.publish(EventType.RAISE_ALARM, test_alarm)
    await asyncio.sleep(0.01)
    await service.handle_controller_message(
        AckAlarmMsg(alarm_occurrence_id=f"tag1@{test_alarm.timestamp.isoformat()}")
    )
    await asyncio.sleep(0.01)

    assert len(updates) == 2
    alarm_update: AlarmUpdateMsg = updates[1]
    assert alarm_update.datapoint_identifier == "tag1"
    assert alarm_update.activation_time is not None
    assert alarm_update.deactivation_time is None
    assert alarm_update.acknowledge_time is not None
    assert alarm_update.isFinished() is False


@pytest.mark.asyncio
async def test_alarm_acknowledge_inactive_finishes():
    bus = EventBus.get_instance()
    model = AlarmModel()
    service = AlarmService(bus, model, controller=None)

    updates = []

    async def capture(data):
        updates.append(data)

    bus.subscribe(EventType.ALARM_UPDATE, capture)

    test_alarm = RaiseAlarmMsg(
        datapoint_identifier="tag1", timestamp=datetime.now(), rule_id="rule1"
    )
    await bus.publish(EventType.RAISE_ALARM, test_alarm)
    await asyncio.sleep(0.01)
    await bus.publish(
        EventType.LOWER_ALARM,
        LowerAlarmMsg(datapoint_identifier="tag1", rule_id="rule1"),
    )
    await asyncio.sleep(0.01)
    await service.handle_controller_message(
        AckAlarmMsg(alarm_occurrence_id=f"tag1@{test_alarm.timestamp.isoformat()}")
    )
    await asyncio.sleep(0.01)

    assert len(updates) == 3
    alarm_update: AlarmUpdateMsg = updates[2]
    assert alarm_update.datapoint_identifier == "tag1"
    assert alarm_update.activation_time is not None
    assert alarm_update.deactivation_time is not None
    assert alarm_update.acknowledge_time is not None
    assert alarm_update.isFinished() is True


@pytest.mark.asyncio
async def test_recursive_alarms_full_updates():
    bus = EventBus.get_instance()
    model = AlarmModel()
    AlarmService(bus, model, controller=None)

    updates = []

    async def capture(data):
        updates.append(data)

    bus.subscribe(EventType.ALARM_UPDATE, capture)

    await bus.publish(
        EventType.RAISE_ALARM,
        RaiseAlarmMsg(datapoint_identifier="door", rule_id="rule1"),
    )
    await asyncio.sleep(0.01)
    await bus.publish(
        EventType.LOWER_ALARM,
        LowerAlarmMsg(datapoint_identifier="door", rule_id="rule1"),
    )
    await asyncio.sleep(0.01)
    await bus.publish(
        EventType.RAISE_ALARM,
        RaiseAlarmMsg(datapoint_identifier="door", rule_id="rule1"),
    )
    await asyncio.sleep(0.01)

    assert len(updates) == 3
    alarm_update1: AlarmUpdateMsg = updates[0]
    alarm_update2: AlarmUpdateMsg = updates[1]
    alarm_update3: AlarmUpdateMsg = updates[2]
    assert alarm_update1.datapoint_identifier == "door"
    assert alarm_update2.datapoint_identifier == "door"
    assert alarm_update3.datapoint_identifier == "door"
    assert alarm_update1.activation_time is not None
    assert alarm_update2.activation_time is not None
    assert alarm_update3.activation_time is not None

    assert alarm_update1.deactivation_time is None
    assert alarm_update2.deactivation_time is not None
    assert alarm_update3.deactivation_time is None
    assert alarm_update1.alarm_occurrence_id == alarm_update2.alarm_occurrence_id
    assert alarm_update1.alarm_occurrence_id != alarm_update3.alarm_occurrence_id


@pytest.mark.asyncio
async def test_alarm_active_inactive_ack():
    bus = EventBus.get_instance()
    model = AlarmModel()
    service = AlarmService(bus, model, controller=None)

    updates = []
    updates = []

    async def capture(data):
        updates.append(data)

    bus.subscribe(EventType.ALARM_UPDATE, capture)

    test_alarm = RaiseAlarmMsg(
        datapoint_identifier="rule1", timestamp=datetime.now(), rule_id="rule1"
    )
    await bus.publish(EventType.RAISE_ALARM, test_alarm)
    await asyncio.sleep(0.01)

    await bus.publish(
        EventType.LOWER_ALARM,
        LowerAlarmMsg(datapoint_identifier="rule1", rule_id="rule1"),
    )
    await asyncio.sleep(0.01)

    await service.handle_controller_message(
        AckAlarmMsg(alarm_occurrence_id=f"rule1@{test_alarm.timestamp.isoformat()}")
    )
    await asyncio.sleep(0.01)

    assert len(updates) == 3
    alarm_update1: AlarmUpdateMsg = updates[0]
    alarm_update2: AlarmUpdateMsg = updates[1]
    alarm_update3: AlarmUpdateMsg = updates[2]

    assert alarm_update1.datapoint_identifier == "rule1"
    assert alarm_update2.datapoint_identifier == "rule1"
    assert alarm_update3.datapoint_identifier == "rule1"

    assert alarm_update1.activation_time is not None
    assert alarm_update2.activation_time is not None
    assert alarm_update3.activation_time is not None

    assert alarm_update1.deactivation_time is None
    assert alarm_update2.deactivation_time is not None
    assert alarm_update3.deactivation_time is not None

    assert alarm_update1.acknowledge_time is None
    assert alarm_update2.acknowledge_time is None
    assert alarm_update3.acknowledge_time is not None

    assert alarm_update1.isFinished() is False
    assert alarm_update2.isFinished() is False
    assert alarm_update3.isFinished() is True
