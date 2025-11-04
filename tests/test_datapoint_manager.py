import pytest
import asyncio
import datetime

from openscada_lite.common.config.config import Config
from openscada_lite.modules.datapoint.model import DatapointModel
from openscada_lite.modules.datapoint.service import DatapointService
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import RawTagUpdateMsg, TagUpdateMsg

@pytest.fixture(autouse=True)
def reset_config_singleton():
    Config.reset_instance()
    Config.get_instance("tests/test_config.json")

def setup_function():
    Config.reset_instance()

#Reset the bus for each test
@pytest.fixture(autouse=True)
def reset_event_bus(monkeypatch):
    # Reset the singleton before each test
    monkeypatch.setattr(EventBus, "_instance", None)

@pytest.mark.asyncio
async def test_update_tag_quality_and_timestamp():
    bus = EventBus.get_instance()
    dp_engine = DatapointService(bus, DatapointModel(), None)
    results = []

    async def capture(msg: TagUpdateMsg):
        results.append(msg)

    bus.subscribe(EventType.TAG_UPDATE, capture)

    now = datetime.datetime.now()
    await dp_engine.handle_controller_message(RawTagUpdateMsg("WaterTank@TANK", 55.5, "bad", now))
    tag = dp_engine.model.get("WaterTank@TANK")
    assert tag.value == 55.5
    assert tag.quality == "bad"
    assert tag.timestamp == now

    await asyncio.sleep(0.01) 
    assert results[0].quality == "bad"
    assert results[0].timestamp == now

@pytest.mark.asyncio
async def test_get_tag_returns_none_for_missing_tag():
    bus = EventBus.get_instance()
    dp_engine = DatapointService(bus, DatapointModel(), None)
    tag = dp_engine.model.get("Server2@NON_EXISTENT")
    assert tag is None

@pytest.mark.asyncio
async def test_multiple_tag_updates():
    bus = EventBus.get_instance()
    dp_engine = DatapointService(bus, DatapointModel(), None)
    results = []

    async def capture(msg: TagUpdateMsg):
        results.append(msg)

    bus.subscribe(EventType.TAG_UPDATE, capture)

    await dp_engine.handle_controller_message(RawTagUpdateMsg("WaterTank@TANK", 10, "good", None))
    await dp_engine.handle_controller_message(RawTagUpdateMsg("WaterTank@TANK", 20, "good", None))
    await dp_engine.handle_controller_message(RawTagUpdateMsg("WaterTank@TANK", 15, "good", None))

    await asyncio.sleep(0.01)
    assert dp_engine.model.get("WaterTank@TANK").value == 15
    assert results[0].value == 10
    assert results[1].value == 20
    assert results[2].value == 15

@pytest.mark.asyncio
async def test_update_tag_without_optional_fields():
    bus = EventBus.get_instance()
    dp_engine = DatapointService(bus, DatapointModel(), None)
    results = []

    async def capture(msg: TagUpdateMsg):
        results.append(msg)

    bus.subscribe(EventType.TAG_UPDATE, capture)

    await dp_engine.handle_controller_message(RawTagUpdateMsg("WaterTank@TANK", 99, "good", None))
    tag = dp_engine.model.get("WaterTank@TANK")
    assert tag.value == 99
    assert tag.quality == "good" # Default quality
    assert tag.timestamp is None

    await asyncio.sleep(0.01)
    assert results[0].value == 99

@pytest.mark.asyncio
async def test_update_invalid_tag():
    bus = EventBus.get_instance()
    dp_engine = DatapointService(bus, DatapointModel(), None)

    # Attempt to update a tag not in config
    await dp_engine.handle_controller_message(RawTagUpdateMsg("ServerX.UNKNOWN_TAG", 42, "bad", None))

    # Should not appear in internal state
    tag = dp_engine.model.get("ServerX.UNKNOWN_TAG")
    assert tag is None
