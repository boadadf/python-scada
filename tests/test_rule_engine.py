import asyncio
import pytest

from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.core.rule.rule_manager import RuleEngine
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.entities import Rule
from openscada_lite.common.models.dtos import SendCommandMsg, RaiseAlarmMsg, LowerAlarmMsg, TagUpdateMsg

@pytest.fixture(autouse=True)
def clear_test():
    EventBus.get_instance().clear_subscribers()
    RuleEngine.reset_instance()

@pytest.mark.asyncio
async def test_send_command_triggered():
    test_bus = EventBus.get_instance()
    engine = RuleEngine.get_instance()
    engine.rules = [
        Rule(
            rule_id="test_command",
            on_condition="Server1@pressure > 50",
            on_actions=["send_command('Server1@VALVE1_POS', 0)"]
        )
    ]
    engine.build_tag_to_rules_index()

    received = []

    async def capture(msg: SendCommandMsg):
        received.append(msg)

    test_bus.subscribe(EventType.SEND_COMMAND, capture)

    # Trigger condition
    await test_bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="Server1@pressure", value=60))
    await asyncio.sleep(0.01)

    assert len(received) == 1
    assert received[0].datapoint_identifier == "Server1@VALVE1_POS"
    assert received[0].value == 0
    assert received[0].command_id is not None


@pytest.mark.asyncio
async def test_alarm_active_inactive():
    test_bus = EventBus.get_instance()
    engine = RuleEngine.get_instance()
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

    alarms_active = []
    alarms_inactive = []

    async def capture_alarm_active(msg: RaiseAlarmMsg):
        alarms_active.append(msg)

    async def capture_alarm_inactive(msg: LowerAlarmMsg):
        alarms_inactive.append(msg)

    test_bus.subscribe(EventType.RAISE_ALARM, capture_alarm_active)
    test_bus.subscribe(EventType.LOWER_ALARM, capture_alarm_inactive)

    # Condition true → alarm_active
    await test_bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="Server1@temperature", value=90))
    await asyncio.sleep(0.01)

    assert len(alarms_active) == 1
    assert alarms_active[0].datapoint_identifier == "Server1@temperature"

    # Condition false → alarm_inactive
    await test_bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="Server1@temperature", value=70))
    await asyncio.sleep(0.01)

    assert len(alarms_inactive) == 1
    assert alarms_inactive[0].datapoint_identifier == "Server1@temperature"


@pytest.mark.asyncio
async def test_multiple_actions():
    test_bus = EventBus.get_instance()
    engine = RuleEngine.get_instance()
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

    commands = []
    alarms = []

    async def capture_command(msg: SendCommandMsg):
        commands.append(msg)

    async def capture_alarm(msg: RaiseAlarmMsg):
        alarms.append(msg)

    test_bus.subscribe(EventType.SEND_COMMAND, capture_command)
    test_bus.subscribe(EventType.RAISE_ALARM, capture_alarm)

    # Trigger condition
    await test_bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="Server1@pressure", value=120))
    await asyncio.sleep(0.01)

    assert len(commands) == 1
    assert commands[0].datapoint_identifier == "Server2@VALVE1_POS"
    assert commands[0].value == 0
    assert len(alarms) == 1
    assert alarms[0].datapoint_identifier == "Server1@pressure"

@pytest.mark.asyncio
async def test_on_action_triggers_every_time_without_off():
    test_bus = EventBus.get_instance()
    engine = RuleEngine.get_instance()
    engine.rules = [
        Rule(
            rule_id="repeat_on_rule",
            on_condition="Server1@level > 10",
            on_actions=["raise_alarm()"]
            # No off_condition
        )
    ]
    engine.build_tag_to_rules_index()

    alarms = []

    async def capture_alarm(msg: RaiseAlarmMsg):
        alarms.append(msg)

    test_bus.subscribe(EventType.RAISE_ALARM, capture_alarm)

    # First trigger
    await test_bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="Server1@level", value=15))
    await asyncio.sleep(0.01)
    # Second trigger (should trigger again)
    await test_bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="Server1@level", value=20))
    await asyncio.sleep(0.01)

    assert len(alarms) == 2
    assert alarms[0].datapoint_identifier == "Server1@level"
    assert alarms[1].datapoint_identifier == "Server1@level"