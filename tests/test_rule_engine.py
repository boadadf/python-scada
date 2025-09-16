import asyncio
import pytest

from app.common.bus.event_bus import EventBus
from app.backend.rule.rule_manager import RuleEngine
from app.common.bus.event_types import EventType
from app.common.models.entities import Rule
from app.common.models.dtos import SendCommandMsg, RaiseAlarmMsg, LowerAlarmMsg, TagUpdateMsg

@pytest.mark.asyncio
async def test_send_command_triggered():
    bus = EventBus()
    engine = RuleEngine(bus)
    engine.rules = [
        Rule(
            rule_id="test_command",
            on_condition="Server1@pressure > 50",
            on_actions=["send_command('Server1@VALVE1_POS', 0)"]
        )
    ]
    engine.build_tag_to_rules_index()
    engine.subscribe_to_eventbus()

    received = []

    async def capture(msg: SendCommandMsg):
        received.append(msg)

    bus.subscribe(EventType.SEND_COMMAND, capture)

    # Trigger condition
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="Server1@pressure", value=60))
    await asyncio.sleep(0.01)

    assert len(received) == 1
    assert received[0].datapoint_identifier == "Server1@VALVE1_POS"
    assert received[0].command == 0
    assert received[0].command_id is not None


@pytest.mark.asyncio
async def test_alarm_active_inactive():
    bus = EventBus()
    engine = RuleEngine(bus)
    engine.rules = [
        Rule(
            rule_id="test_alarm",
            on_condition="Server1@temperature > 80",
            on_actions=["raise_alarm()"],
            off_condition="Server1@temperature <= 70",
            off_actions=["lower_alarm()"]
        )
    ]
    engine.build_tag_to_rules_index()
    engine.subscribe_to_eventbus()

    alarms_active = []
    alarms_inactive = []

    async def capture_alarm_active(msg: RaiseAlarmMsg):
        alarms_active.append(msg)

    async def capture_alarm_inactive(msg: LowerAlarmMsg):
        alarms_inactive.append(msg)

    bus.subscribe(EventType.RAISE_ALARM, capture_alarm_active)
    bus.subscribe(EventType.LOWER_ALARM, capture_alarm_inactive)

    # Condition true → alarm_active
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="Server1@temperature", value=90))
    await asyncio.sleep(0.01)

    assert len(alarms_active) == 1
    assert alarms_active[0].datapoint_identifier == "Server1@temperature"

    # Condition false → alarm_inactive
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="Server1@temperature", value=70))
    await asyncio.sleep(0.01)

    assert len(alarms_inactive) == 1
    assert alarms_inactive[0].datapoint_identifier == "Server1@temperature"


@pytest.mark.asyncio
async def test_multiple_actions():
    bus = EventBus()
    engine = RuleEngine(bus)
    engine.rules = [
        Rule(
            rule_id="multi_action_rule",
            on_condition="Server1@pressure > 100",
            on_actions=[
                "send_command('Server2@VALVE1_POS', 0)",
                "raise_alarm('Server1@pressure')"
            ]
        )
    ]
    engine.build_tag_to_rules_index()
    engine.subscribe_to_eventbus()

    commands = []
    alarms = []

    async def capture_command(msg: SendCommandMsg):
        commands.append(msg)

    async def capture_alarm(msg: RaiseAlarmMsg):
        alarms.append(msg)

    bus.subscribe(EventType.SEND_COMMAND, capture_command)
    bus.subscribe(EventType.RAISE_ALARM, capture_alarm)

    # Trigger condition
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="Server1@pressure", value=120))
    await asyncio.sleep(0.01)

    assert len(commands) == 1
    assert commands[0].datapoint_identifier == "Server2@VALVE1_POS"
    assert commands[0].command == 0
    assert len(alarms) == 1
    assert alarms[0].datapoint_identifier == "Server1@pressure"

@pytest.mark.asyncio
async def test_on_action_triggers_every_time_without_off():
    bus = EventBus()
    engine = RuleEngine(bus)
    engine.rules = [
        Rule(
            rule_id="repeat_on_rule",
            on_condition="Server1@level > 10",
            on_actions=["raise_alarm()"]
            # No off_condition
        )
    ]
    engine.build_tag_to_rules_index()
    engine.subscribe_to_eventbus()

    alarms = []

    async def capture_alarm(msg: RaiseAlarmMsg):
        alarms.append(msg)

    bus.subscribe(EventType.RAISE_ALARM, capture_alarm)

    # First trigger
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="Server1@level", value=15))
    await asyncio.sleep(0.01)
    # Second trigger (should trigger again)
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="Server1@level", value=20))
    await asyncio.sleep(0.01)

    assert len(alarms) == 2
    assert alarms[0].datapoint_identifier == "Server1@level"
    assert alarms[1].datapoint_identifier == "Server1@level"