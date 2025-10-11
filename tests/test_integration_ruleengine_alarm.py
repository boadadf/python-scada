import asyncio
import pytest
from datetime import datetime

from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.entities import Rule
from openscada_lite.common.models.dtos import TagUpdateMsg, AlarmUpdateMsg
from openscada_lite.core.rule.rule_manager import RuleEngine
from openscada_lite.modules.alarm.model import AlarmModel
from openscada_lite.modules.alarm.service import AlarmService


@pytest.fixture(autouse=True)
def clear_singletons(monkeypatch):
    # Ensure clean environment for each test
   # monkeypatch.setattr(EventBus, "_instance", None)
    RuleEngine.reset_instance()


@pytest.mark.asyncio
async def test_integration_switch_rules_alarm_lifecycle():
    """
    Full integration test:
    1. Create RuleEngine + AlarmService sharing same EventBus
    2. Simulate tag changes for switch_error_turn / switch_error_straight
    3. Verify alarm activation/deactivation cycles correctly
    """

    # --- Setup core components ---
    bus = EventBus.get_instance()    
    bus.clear_subscribers()
    model = AlarmModel()
    AlarmService(bus, model, controller=None)
    engine = RuleEngine.get_instance(bus)

    # --- Define two mutually exclusive rules ---
    engine.rules = [
        Rule(
            rule_id="switch_error_straight",
            on_condition="TrainTestDriver@RIGHT_SWITCH_CONTROL == 'STRAIGHT' and TrainTestDriver@LEFT_SWITCH_CONTROL == 'TURN'",
            on_actions=["raise_alarm()"],
            off_condition="not (TrainTestDriver@RIGHT_SWITCH_CONTROL == 'STRAIGHT' and TrainTestDriver@LEFT_SWITCH_CONTROL == 'TURN')",
            off_actions=["lower_alarm()"]
        ),
        Rule(
            rule_id="switch_error_turn",
            on_condition="TrainTestDriver@RIGHT_SWITCH_CONTROL == 'TURN' and TrainTestDriver@LEFT_SWITCH_CONTROL == 'STRAIGHT'",
            on_actions=["raise_alarm()"],
            off_condition="not (TrainTestDriver@RIGHT_SWITCH_CONTROL == 'TURN' and TrainTestDriver@LEFT_SWITCH_CONTROL == 'STRAIGHT')",
            off_actions=["lower_alarm()"]
        )
    ]
    engine.build_tag_to_rules_index()

    # --- Collect AlarmUpdate events ---
    updates = []

    async def capture(msg: AlarmUpdateMsg):
        updates.append(msg)

    bus.subscribe(EventType.ALARM_UPDATE, capture)

    # --- Simulate condition for switch_error_turn ---
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="TrainTestDriver@RIGHT_SWITCH_CONTROL", value="TURN"))
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="TrainTestDriver@LEFT_SWITCH_CONTROL", value="STRAIGHT"))
    await asyncio.sleep(0.05)

    assert len(updates) >= 1
    first = updates[-1]
    assert first.datapoint_identifier in ("TrainTestDriver@RIGHT_SWITCH_CONTROL", "TrainTestDriver@LEFT_SWITCH_CONTROL")
    assert first.activation_time is not None
    assert first.deactivation_time is None

    # --- Now simulate transition that should deactivate the first rule and activate the second ---
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="TrainTestDriver@RIGHT_SWITCH_CONTROL", value="STRAIGHT"))
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="TrainTestDriver@LEFT_SWITCH_CONTROL", value="TURN"))
    await asyncio.sleep(0.05)

    # We should now have an update showing a deactivation, followed by a new activation
    assert len(updates) >= 3
    deactivation = updates[-2]
    activation_2 = updates[-1]

    assert deactivation.deactivation_time is not None
    assert activation_2.deactivation_time is None
    assert activation_2.activation_time is not None

    # --- Finally, clear both conditions (no error state) ---
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="TrainTestDriver@RIGHT_SWITCH_CONTROL", value="STRAIGHT"))
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="TrainTestDriver@LEFT_SWITCH_CONTROL", value="STRAIGHT"))
    await asyncio.sleep(0.05)

    # The last update should have both activation and deactivation time
    last = updates[-1]
    assert last.activation_time is not None
    assert last.deactivation_time is not None


@pytest.mark.asyncio
async def test_reactivation_creates_new_occurrence():
    """
    Ensure a new alarm occurrence is created after full deactivate -> activate cycle.
    """

    bus = EventBus.get_instance()
    model = AlarmModel()
    AlarmService(bus, model, controller=None)
    engine = RuleEngine.get_instance(bus)

    engine.rules = [
        Rule(
            rule_id="test_reactivate",
            on_condition="X@pos == 'A'",
            on_actions=["raise_alarm()"],
            off_condition="X@pos != 'A'",
            off_actions=["lower_alarm()"]
        )
    ]
    engine.build_tag_to_rules_index()

    updates = []

    async def capture(msg: AlarmUpdateMsg):
        updates.append(msg)

    bus.subscribe(EventType.ALARM_UPDATE, capture)

    # Activate once
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="X@pos", value="A"))
    await asyncio.sleep(0.01)
    # Deactivate
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="X@pos", value="B"))
    await asyncio.sleep(0.01)
    # Reactivate
    await bus.publish(EventType.TAG_UPDATE, TagUpdateMsg(datapoint_identifier="X@pos", value="A"))
    await asyncio.sleep(0.01)

    assert len(updates) >= 3
    first_occurrence = updates[0].alarm_occurrence_id
    second_occurrence = updates[-1].alarm_occurrence_id
    assert first_occurrence != second_occurrence
