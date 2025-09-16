import uuid
import pytest
import asyncio
from app.common import bus
from app.common.bus.event_bus import EventBus
from app.frontend.datapoints.model import DatapointModel
from app.frontend.datapoints.service import DatapointService
from app.backend.communications.connector_manager import ConnectorManager
from app.backend.rule.rule_manager import RuleEngine
from app.backend.alarm.alarm_engine import AlarmEngine
from app.common.bus.event_types import EventType
from app.common.models.dtos import CommandFeedbackMsg, LowerAlarmMsg, RaiseAlarmMsg, SendCommandMsg
from app.common.config.config import Config

@pytest.fixture(autouse=True)
def reset_config_singleton():
    Config.reset_instance()
    Config.get_instance("tests/test_config.json")

def setup_function():
    Config.reset_instance()

@pytest.mark.asyncio
async def test_full_system_with_recursive_alarms_and_feedback():
    # EventBus
    bus = EventBus()

    # Datapoint Engine
    dp_engine = DatapointService(bus, DatapointModel(), None)

    # Configuration & Connector
    Config.reset_instance()
    config = Config.get_instance("tests/test_config.json")
    connector_manager = ConnectorManager(bus, config.get_drivers())
    await connector_manager.start_all()

    # Rule Engine
    rule_engine = RuleEngine(bus)
    rule_engine.load_rules()
    rule_engine.subscribe_to_eventbus()

    # Alarm Engine
    alarm_engine = AlarmEngine(bus)

    # Capture outputs
    commands = []
    alarms_active = []
    alarms_inactive = []
    feedback = []

    async def capture_command(msg: SendCommandMsg):
        commands.append(msg)

    async def capture_alarm_active(msg: RaiseAlarmMsg):
        alarms_active.append(msg)

    async def capture_alarm_inactive(msg: LowerAlarmMsg):
        alarms_inactive.append(msg)

    async def capture_feedback(msg: CommandFeedbackMsg):
        feedback.append(msg)

    bus.subscribe(EventType.SEND_COMMAND, capture_command)
    bus.subscribe(EventType.RAISE_ALARM, capture_alarm_active)
    bus.subscribe(EventType.LOWER_ALARM, capture_alarm_inactive)
    bus.subscribe(EventType.COMMAND_FEEDBACK, capture_feedback)

    driver = connector_manager.drivers[1]["driver"]

    # --- Simulate driver updates ---
    # Trigger first alarm    
    await driver.simulate_value("PRESSURE", 120)

    # Alarm is deactivated
    await driver.simulate_value("PRESSURE", 70)

    # Alarm is activated again -> 2nd instance is created
    await driver.simulate_value("PRESSURE", 140)
    await asyncio.sleep(0.05)

    # Send a command through connector
    await connector_manager.send_command("Server2", "VALVE1_POS", 0, uuid.uuid4())
    await asyncio.sleep(0.05)

    # Command feedback captured
    assert len(feedback) > 0
    assert any(fb.datapoint_identifier == "Server2@VALVE1_POS" for fb in feedback)

    # Alarms captured (recursive)
    # Expect at least 2 active occurrences
    active_occurrences = []
    for snapshot in alarms_active:
        if hasattr(snapshot, "datapoint_identifier"):
            active_occurrences.append(snapshot)
        elif isinstance(snapshot, list):
            active_occurrences.extend(snapshot)

    # --- Alarms captured (recursive) ---
    # Expect at least 2 active occurrences
    high_pressure_alarms = [
        a for a in alarms_active if hasattr(a, "datapoint_identifier") and a.datapoint_identifier == "Server2@PRESSURE"
    ]
    assert len(high_pressure_alarms) == 2

    # --- Check inactive alarms ---
    inactive_occurrences = [
        a for a in alarms_inactive if hasattr(a, "datapoint_identifier") and a.datapoint_identifier == "Server2@PRESSURE"
    ]
    assert len(inactive_occurrences) >= 1