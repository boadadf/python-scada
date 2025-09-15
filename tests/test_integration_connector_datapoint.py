import asyncio
import uuid
import pytest
from common.bus.event_bus import EventBus
from frontend.tags.model import DatapointModel
from frontend.tags.service import DatapointService
from backend.communications.drivers.test_driver import TestDriver
from backend.communications.connector_manager import ConnectorManager
from common.bus.event_types import COMMAND_FEEDBACK
from app.common.models.dtos import CommandFeedbackMsg
from common.config.config import Config

@pytest.fixture(autouse=True)
def reset_config_singleton():
    Config.reset_instance()
    Config.get_instance("tests/test_config.json")

def setup_function():
    Config.reset_instance()


@pytest.mark.asyncio
async def test_connector_drivers_publish_to_datapoint_engine():
    bus = EventBus()
    dp_engine = DatapointService(bus, DatapointModel(), None)

    config = Config.get_instance()
    drivers_config = config.get_drivers()
    connector_manager = ConnectorManager(bus, drivers_config)

    await connector_manager.start_all()

    # Let TestDrivers publish some values
    await asyncio.sleep(2)

    # Check that DatapointEngine received updates
    all_tags = dp_engine.model.get_all_tags()
    assert len(all_tags) > 0
    for tag_id in all_tags:
        assert all_tags[tag_id].value is not None

    # Stop drivers
    await connector_manager.stop_all()

@pytest.mark.asyncio
async def test_send_command_routing():
    bus = EventBus()
    dp_engine = DatapointService(bus, DatapointModel(), None)

    config = Config.get_instance()
    drivers_config = config.get_drivers()
    connector_manager = ConnectorManager(bus, drivers_config)

    await connector_manager.start_all()
    
    # Prepare feedback capture BEFORE sending the command
    feedback = []
    async def capture(msg):
        # Accept both dict and CommandFeedbackMsg for robustness
        if isinstance(msg, dict):
            msg = CommandFeedbackMsg(**msg)
        feedback.append(msg)
    bus.subscribe(COMMAND_FEEDBACK, capture)
    
    command_id = uuid.uuid4()
    # Send a command to Server1@TANK1_LEVEL
    await connector_manager.send_command("Server1", "TANK1_LEVEL", 99, command_id)

    # Wait for feedback
    await asyncio.sleep(0.2)

    assert len(feedback) > 0, "No command feedback received"
    assert feedback[0].status == "OK"
    assert feedback[0].command_id is not None

    await connector_manager.stop_all()
