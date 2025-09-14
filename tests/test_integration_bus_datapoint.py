import asyncio
import pytest
from common.bus.event_bus import EventBus
from backend.datapoints.datapoint_manager import DatapointEngine
from app.common.bus.event_types import TAG_UPDATE
from app.common.models.dtos import TagUpdateMsg
from common.config.config import Config

@pytest.mark.asyncio
async def test_driver_to_datapoint_integration():
    bus = EventBus()
    dp_engine = DatapointEngine(bus)
    dp_engine.subscribe_to_eventbus()

    # Use namespaced IDs from config
    config = Config.get_instance()
    driver_name = config.get_drivers()[0]["name"]  # e.g., "Server1"
    tag_id = f"{driver_name}@TANK1_LEVEL"

    received = []

    async def rule_engine_sim(msg: TagUpdateMsg):
        received.append(msg)

    bus.subscribe(TAG_UPDATE, rule_engine_sim)

    # Simulate a driver publishing a tag update with correct namespaced tag_id
    await bus.publish(TAG_UPDATE, TagUpdateMsg(tag_id=tag_id, value=75.5))
    await asyncio.sleep(0.01)

    # DatapointEngine updated internal state
    tag = dp_engine.get_tag(tag_id)
    assert tag["value"] == 75.5

    # RuleEngine also received update
    assert received[0].tag_id == tag_id
    assert received[0].value == 75.5

@pytest.mark.asyncio
async def test_publish_initial_state():
    bus = EventBus()
    dp_engine = DatapointEngine(bus)
    dp_engine.subscribe_to_eventbus()

    # Use namespaced IDs from config
    config = Config.get_instance()
    driver_name = config.get_drivers()[0]["name"]  # e.g., "Server1"

    tag1 = f"{driver_name}@TANK1_LEVEL"
    tag2 = f"{driver_name}@PUMP1_STATUS"

    await dp_engine.update_tag(tag1, 50)
    await dp_engine.update_tag(tag2, "OFF")

    captured = []
    async def capture(msg: TagUpdateMsg):
        captured.append(msg)
    bus.subscribe(TAG_UPDATE, capture)

    # Trigger initial state via EventBus special message
    await bus.publish("request_initial_state", None)
    await asyncio.sleep(0.05)

    assert any(d.tag_id == tag1 and d.value == 50 for d in captured)
    assert any(d.tag_id == tag2 and d.value == "OFF" for d in captured)

