import asyncio
import pytest
from backend.event_bus import EventBus

@pytest.mark.asyncio
async def test_publish_and_subscribe():
    bus = EventBus()
    results = []

    async def callback(data):
        results.append(data)

    bus.subscribe("test_event", callback)
    await bus.publish("test_event", {"value": 42})
    await asyncio.sleep(0.01)
    assert results == [{"value": 42}]

@pytest.mark.asyncio
async def test_multiple_subscribers():
    bus = EventBus()
    results1 = []
    results2 = []

    async def callback1(data):
        results1.append(data)

    async def callback2(data):
        results2.append(data)

    bus.subscribe("event1", callback1)
    bus.subscribe("event1", callback2)
    await bus.publish("event1", 123)
    await asyncio.sleep(0.01)
    assert results1 == [123]
    assert results2 == [123]

@pytest.mark.asyncio
async def test_unsubscribe():
    bus = EventBus()
    results = []

    async def callback(data):
        results.append(data)

    bus.subscribe("event1", callback)
    bus.unsubscribe("event1", callback)
    await bus.publish("event1", 999)
    await asyncio.sleep(0.01)
    assert results == []

@pytest.mark.asyncio
async def test_publish_no_subscribers():
    bus = EventBus()
    # Should not raise any error
    await bus.publish("non_existing_event", {"ok": True})

