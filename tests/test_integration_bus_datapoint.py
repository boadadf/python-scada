import asyncio
import pytest
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.modules.datapoint.model import DatapointModel
from openscada_lite.modules.datapoint.service import DatapointService
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import RawTagUpdateMsg, TagUpdateMsg
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
async def test_driver_to_datapoint_integration():
    bus = EventBus.get_instance()
    dp_engine = DatapointService(bus, DatapointModel(), None)
    
    # Use namespaced IDs from config
    config = Config.get_instance()
    driver_name = config.get_drivers()[0]["name"]  # e.g., "Server1"
    tag_id = f"{driver_name}@TANK"

    received = []

    async def rule_engine_sim(msg: TagUpdateMsg):
        received.append(msg)

    bus.subscribe(EventType.RAW_TAG_UPDATE, rule_engine_sim)

    # Simulate a driver publishing a tag update with correct namespaced tag_id
    await bus.publish(EventType.RAW_TAG_UPDATE, RawTagUpdateMsg(datapoint_identifier=tag_id, value=75.5))
    await asyncio.sleep(0.01)

    # DatapointEngine updated internal state
    tag = dp_engine.model.get(tag_id)
    assert tag.value == 75.5

    # RuleEngine also received update
    assert received[0].datapoint_identifier == tag_id
    assert received[0].value == 75.5