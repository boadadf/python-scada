import asyncio
import uuid
import pytest
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.modules.datapoint.model import DatapointModel
from openscada_lite.modules.datapoint.service import DatapointService
from core.communications.drivers.test.test_driver import TestDriver
from openscada_lite.core.communications.connector_manager import ConnectorManager
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import CommandFeedbackMsg, SendCommandMsg
from openscada_lite.common.config.config import Config

#Reset the bus for each test
@pytest.fixture(autouse=True)
def reset_event_bus(monkeypatch):
    # Reset the singleton before each test
    monkeypatch.setattr(EventBus, "_instance", None)

@pytest.fixture(autouse=True)
def reset_config_singleton():
    Config.reset_instance()
    Config.get_instance("tests/test_config.json")

def setup_function():
    Config.reset_instance()


@pytest.mark.asyncio
async def test_connector_drivers_publish_to_datapoint_engine():
    bus = EventBus.get_instance()
    dp_engine = DatapointService(bus, DatapointModel(), None)   
    connector_manager = ConnectorManager(bus)
    await connector_manager.init_drivers()
    print("ConnectorManager initialized.")
    await connector_manager.start_all()
    print("ConnectorManager and DatapointService started.")
    # Let TestDrivers publish some values
    await asyncio.sleep(2)

    # Check that DatapointEngine received updates
    all_tags = dp_engine.model.get_all()
    assert len(all_tags) > 0
    for tag_id in all_tags:
        assert all_tags[tag_id].value is not None

    # Stop drivers
    await connector_manager.stop_all()

@pytest.mark.asyncio
async def test_send_command_routing():
    bus = EventBus.get_instance()    

    connector_manager = ConnectorManager(bus)
    
    await connector_manager.start_all()
    
    # Prepare feedback capture BEFORE sending the command
    feedback = []
    event = asyncio.Event()
    async def capture(msg):
        # Accept both dict and CommandFeedbackMsg for robustness
        if isinstance(msg, dict):
            msg = CommandFeedbackMsg(**msg)
        feedback.append(msg)
        event.set()
    bus.subscribe(EventType.COMMAND_FEEDBACK, capture)
    
    command_id = uuid.uuid4()
    # Send a command to Server1@TANK1_LEVEL
    await connector_manager.send_command(SendCommandMsg(command_id, "Server1@TANK", 99))

    # Wait for feedback
    await asyncio.wait_for(event.wait(), timeout=2.0)

    assert len(feedback) > 0, "No command feedback received"
    assert feedback[0].feedback == "OK"
    assert feedback[0].command_id is not None

    await connector_manager.stop_all()
