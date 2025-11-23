import asyncio
import pytest

from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.modules.rule.manager.rule_manager import RuleEngine
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.entities import Rule
from openscada_lite.common.models.dtos import (
    SendCommandMsg,
    RaiseAlarmMsg,
    LowerAlarmMsg,
    TagUpdateMsg,
)


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
            on_condition="WaterTank@pressure > 50",
            on_actions=["send_command('WaterTank@VALVE1_POS', 0)"],
        )
    ]
    engine.build_tag_to_rules_index()

    received = []

    async def capture(msg: SendCommandMsg):
        received.append(msg)

    test_bus.subscribe(EventType.SEND_COMMAND, capture)

    # Trigger condition
    await test_bus.publish(
        EventType.TAG_UPDATE,
        TagUpdateMsg(datapoint_identifier="WaterTank@pressure", value=60),
    )
    await asyncio.sleep(0.01)

    assert len(received) == 1
    assert received[0].datapoint_identifier == "WaterTank@VALVE1_POS"
    assert received[0].value == 0
    assert received[0].command_id is not None


@pytest.mark.asyncio
async def test_alarm_active_inactive():
    test_bus = EventBus.get_instance()
    engine = RuleEngine.get_instance()
    engine.rules = [
        Rule(
            rule_id="test_alarm",
            on_condition="WaterTank@temperature > 80",
            on_actions=["raise_alarm()"],
            off_condition="WaterTank@temperature <= 70",
            off_actions=["lower_alarm()"],
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
    await test_bus.publish(
        EventType.TAG_UPDATE,
        TagUpdateMsg(datapoint_identifier="WaterTank@temperature", value=90),
    )
    await asyncio.sleep(0.01)

    assert len(alarms_active) == 1
    assert alarms_active[0].datapoint_identifier == "WaterTank@temperature"

    # Condition false → alarm_inactive
    await test_bus.publish(
        EventType.TAG_UPDATE,
        TagUpdateMsg(datapoint_identifier="WaterTank@temperature", value=70),
    )
    await asyncio.sleep(0.01)

    assert len(alarms_inactive) == 1
    assert alarms_inactive[0].datapoint_identifier == "WaterTank@temperature"


@pytest.mark.asyncio
async def test_multiple_actions():
    test_bus = EventBus.get_instance()
    engine = RuleEngine.get_instance()
    engine.rules = [
        Rule(
            rule_id="multi_action_rule",
            on_condition="WaterTank@pressure > 100",
            on_actions=[
                "send_command('AuxServer@VALVE1_POS', 0)",
                "raise_alarm('WaterTank@pressure')",
            ],
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
    await test_bus.publish(
        EventType.TAG_UPDATE,
        TagUpdateMsg(datapoint_identifier="WaterTank@pressure", value=120),
    )
    await asyncio.sleep(0.01)

    assert len(commands) == 1
    assert commands[0].datapoint_identifier == "AuxServer@VALVE1_POS"
    assert commands[0].value == 0
    assert len(alarms) == 1
    assert alarms[0].datapoint_identifier == "WaterTank@pressure"


@pytest.mark.asyncio
async def test_on_action_triggers_twice_only_onc_alarm():
    test_bus = EventBus.get_instance()
    engine = RuleEngine.get_instance()
    engine.rules = [
        Rule(
            rule_id="repeat_on_rule",
            on_condition="WaterTank@level > 10",
            on_actions=["raise_alarm()"],
            # No off_condition
        )
    ]
    engine.build_tag_to_rules_index()

    alarms = []

    async def capture_alarm(msg: RaiseAlarmMsg):
        alarms.append(msg)

    test_bus.subscribe(EventType.RAISE_ALARM, capture_alarm)

    # First trigger
    await test_bus.publish(
        EventType.TAG_UPDATE,
        TagUpdateMsg(datapoint_identifier="WaterTank@level", value=15),
    )
    await asyncio.sleep(0.01)
    # Second trigger (should trigger again)
    await test_bus.publish(
        EventType.TAG_UPDATE,
        TagUpdateMsg(datapoint_identifier="WaterTank@level", value=20),
    )
    await asyncio.sleep(0.01)

    assert len(alarms) == 1
    assert alarms[0].datapoint_identifier == "WaterTank@level"


@pytest.mark.asyncio
async def test_switch_error_rules_toggle():
    """
    Verify that switch_error_straight and switch_error_turn rules correctly
    activate and deactivate depending on LEFT/RIGHT switch values.
    """
    test_bus = EventBus.get_instance()
    engine = RuleEngine.get_instance()
    engine.rules = [
        Rule(
            rule_id="switch_error_straight",
            on_condition="TrainTestDriver@RIGHT_SWITCH_CONTROL == 'STRAIGHT' "
            "and TrainTestDriver@LEFT_SWITCH_CONTROL == 'TURN'",
            on_actions=["raise_alarm()"],
        ),
        Rule(
            rule_id="switch_error_turn",
            on_condition="TrainTestDriver@RIGHT_SWITCH_CONTROL == 'TURN' "
            "and TrainTestDriver@LEFT_SWITCH_CONTROL == 'STRAIGHT'",
            on_actions=["raise_alarm()"],
        ),
    ]
    engine.build_tag_to_rules_index()

    raised = []
    lowered = []

    async def capture_raise(msg: RaiseAlarmMsg):
        raised.append((msg.datapoint_identifier, msg.rule_id))

    async def capture_lower(msg: LowerAlarmMsg):
        lowered.append((msg.datapoint_identifier, msg.rule_id))

    test_bus.subscribe(EventType.RAISE_ALARM, capture_raise)
    test_bus.subscribe(EventType.LOWER_ALARM, capture_lower)

    # --- 1. Both STRAIGHT initially -> no alarms
    await test_bus.publish(
        EventType.TAG_UPDATE,
        TagUpdateMsg(datapoint_identifier="TrainTestDriver@LEFT_SWITCH_CONTROL", value="STRAIGHT"),
    )
    await test_bus.publish(
        EventType.TAG_UPDATE,
        TagUpdateMsg(
            datapoint_identifier="TrainTestDriver@RIGHT_SWITCH_CONTROL",
            value="STRAIGHT",
        ),
    )
    await asyncio.sleep(0.01)
    assert raised == []
    assert lowered == []

    # --- 2. Right TURN, Left STRAIGHT -> switch_error_turn should activate
    await test_bus.publish(
        EventType.TAG_UPDATE,
        TagUpdateMsg(datapoint_identifier="TrainTestDriver@RIGHT_SWITCH_CONTROL", value="TURN"),
    )
    await asyncio.sleep(0.01)
    assert any(r[1] == "switch_error_turn" for r in raised)

    # --- 3. Now Left TURN, Right TURN -> error_turn should deactivate,
    #  error_straight should NOT activate
    await test_bus.publish(
        EventType.TAG_UPDATE,
        TagUpdateMsg(datapoint_identifier="TrainTestDriver@LEFT_SWITCH_CONTROL", value="TURN"),
    )
    await asyncio.sleep(0.01)
    # should deactivate switch_error_turn
    assert any(lowered_alarm[1] == "switch_error_turn" for lowered_alarm in lowered)
    # and not raise straight alarm
    assert not any(r[1] == "switch_error_straight" for r in raised if r[1] != "switch_error_turn")

    # --- 4. Right STRAIGHT, Left TURN -> now switch_error_straight should activate
    await test_bus.publish(
        EventType.TAG_UPDATE,
        TagUpdateMsg(
            datapoint_identifier="TrainTestDriver@RIGHT_SWITCH_CONTROL",
            value="STRAIGHT",
        ),
    )
    await asyncio.sleep(0.01)
    assert any(r[1] == "switch_error_straight" for r in raised)

    # --- 5. Both STRAIGHT again -> switch_error_straight should deactivate
    await test_bus.publish(
        EventType.TAG_UPDATE,
        TagUpdateMsg(datapoint_identifier="TrainTestDriver@LEFT_SWITCH_CONTROL", value="STRAIGHT"),
    )
    await asyncio.sleep(0.01)
    assert any(lowered_alarm[1] == "switch_error_straight" for lowered_alarm in lowered)
