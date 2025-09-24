import uuid
import pytest
import asyncio
from openscada_lite.modules.alarm.model import AlarmModel
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.modules.datapoint.model import DatapointModel
from openscada_lite.modules.datapoint.service import DatapointService
from openscada_lite.core.communications.connector_manager import ConnectorManager
from openscada_lite.core.rule.rule_manager import RuleEngine
from openscada_lite.modules.alarm.service import AlarmService
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import CommandFeedbackMsg, LowerAlarmMsg, RaiseAlarmMsg, SendCommandMsg
from openscada_lite.common.config.config import Config

#Reset the bus for each test
@pytest.fixture(autouse=True)
def reset_event_bus(monkeypatch):
    # Reset the singleton before each test
    Config.get_instance("tests/test_config.json")

@pytest.mark.asyncio
async def test_full_system_with_recursive_alarms_and_feedback():
    # EventBus
    bus = EventBus.get_instance()

    model = AlarmModel()
    AlarmService(bus, model, controller=None)

    datapointModel = DatapointModel()
    DatapointService(bus, datapointModel, controller=None)

    # Configuration & Connector
    Config.reset_instance()
    connector_manager = ConnectorManager(bus)
    await connector_manager.start_all()

    # Rule Engine
    RuleEngine.get_instance()

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

    async def capture_feedback(msg):
        if isinstance(msg, dict):
            msg = CommandFeedbackMsg(**msg)
        feedback.append(msg)

    bus.subscribe(EventType.SEND_COMMAND, capture_command)
    bus.subscribe(EventType.RAISE_ALARM, capture_alarm_active)
    bus.subscribe(EventType.LOWER_ALARM, capture_alarm_inactive)
    bus.subscribe(EventType.COMMAND_FEEDBACK, capture_feedback)

    driver = connector_manager.driver_instances["Server2"]

    # --- Simulate driver updates ---
    # Trigger first alarm    
    await driver.simulate_value("PRESSURE", 120)

    # Alarm is deactivated
    await driver.simulate_value("PRESSURE", 70)

    # Alarm is activated again -> 2nd instance is created
    await driver.simulate_value("PRESSURE", 140)
    await asyncio.sleep(0.05)

    # Send a command through connector
    await connector_manager.send_command(SendCommandMsg(uuid.uuid4(), "Server2@VALVE1_POS", 0))
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