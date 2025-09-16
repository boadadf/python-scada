import asyncio
import pytest
from app.common.bus.event_bus import EventBus
from app.frontend.datapoints.model import DatapointModel
from app.frontend.datapoints.service import DatapointService
from app.common.bus.event_types import EventType
from app.common.models.dtos import TagUpdateMsg
from app.common.config.config import Config

@pytest.fixture(autouse=True)
def reset_config_singleton():
    Config.reset_instance()
    Config.get_instance("tests/test_config.json")

def setup_function():
    Config.reset_instance()

@pytest.mark.asyncio
async def test_driver_to_datapoint_integration():
    bus = EventBus()
    dp_engine = DatapointService(bus, DatapointModel(), None)
    
    # Use namespaced IDs from config
    config = Config.get_instance()
    driver_name = config.get_drivers()[0]["name"]  # e.g., "Server1"
    tag_id = f"{driver_name}@TANK1_LEVEL"

    received = []

    async def rule_engine_sim(msg: TagUpdateMsg):
        received.append(msg)

    bus.subscribe(EventType.TAG_UPDATE, rule_engine_sim)

    # Simulate a driver publishing a tag update with correct namespaced tag_id
    await bus.publish(EventType.RAW_TAG_UPDATE, TagUpdateMsg(datapoint_identifier=tag_id, value=75.5))
    await asyncio.sleep(0.01)

    # DatapointEngine updated internal state
    tag = dp_engine.model.get_tag(tag_id)
    assert tag.value == 75.5

    # RuleEngine also received update
    assert received[0].datapoint_identifier == tag_id
    assert received[0].value == 75.5