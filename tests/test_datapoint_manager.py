import pytest
import asyncio

from frontend.datapoints.service import DatapointService
from common.bus.event_bus import EventBus
from app.common.bus.event_types import TAG_UPDATE
from app.common.models.dtos import TagUpdateMsg

@pytest.mark.asyncio
async def test_update_tag_quality_and_timestamp():
    bus = EventBus()
    dp_engine = DatapointService(bus)
    results = []

    async def capture(msg: TagUpdateMsg):
        results.append(msg)

    bus.subscribe(TAG_UPDATE, capture)

    await dp_engine.update_tag("Server1@TANK1_LEVEL", 55.5, quality="bad", timestamp="2025-09-11T08:30:00Z")
    tag = dp_engine.get_tag("Server1@TANK1_LEVEL")
    assert tag.value == 55.5
    assert tag.quality == "bad"
    assert tag.timestamp == "2025-09-11T08:30:00Z"

    await asyncio.sleep(0.01)
    assert results[0].quality == "bad"
    assert results[0].timestamp == "2025-09-11T08:30:00Z"

@pytest.mark.asyncio
async def test_get_tag_returns_none_for_missing_tag():
    bus = EventBus()
    dp_engine = DatapointService(bus)
    tag = dp_engine.get_tag("Server2@NON_EXISTENT")
    assert tag is None

@pytest.mark.asyncio
async def test_multiple_tag_updates():
    bus = EventBus()
    dp_engine = DatapointService(bus)
    results = []

    async def capture(msg: TagUpdateMsg):
        results.append(msg)

    bus.subscribe(TAG_UPDATE, capture)

    await dp_engine.update_tag("Server1@TANK1_LEVEL", 10)
    await dp_engine.update_tag("Server1@TANK1_LEVEL", 20)
    await dp_engine.update_tag("Server1@TANK1_LEVEL", 15)

    await asyncio.sleep(0.01)
    assert dp_engine.get_tag("Server1@TANK1_LEVEL").value == 15
    assert results[0].value == 10
    assert results[1].value == 20
    assert results[2].value == 15

@pytest.mark.asyncio
async def test_update_tag_without_optional_fields():
    bus = EventBus()
    dp_engine = DatapointService(bus)
    results = []

    async def capture(msg: TagUpdateMsg):
        results.append(msg)

    bus.subscribe(TAG_UPDATE, capture)

    await dp_engine.update_tag("Server1@TANK1_LEVEL", 99)
    tag = dp_engine.get_tag("Server1@TANK1_LEVEL")
    assert tag.value == 99
    assert tag.quality == "good" # Default quality
    assert tag.timestamp is None

    await asyncio.sleep(0.01)
    assert results[0].value == 99

@pytest.mark.asyncio
async def test_update_invalid_tag():
    bus = EventBus()
    dp_engine = DatapointService(bus)

    # Attempt to update a tag not in config
    await dp_engine.update_tag("ServerX.UNKNOWN_TAG", 42)

    # Should not appear in internal state
    tag = dp_engine.get_tag("ServerX.UNKNOWN_TAG")
    assert tag is None
