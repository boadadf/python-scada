import asyncio
import pytest
from common.bus.event_bus import EventBus
from app.common.bus.event_types import TAG_UPDATE
from app.common.models.dtos import TagUpdateMsg

@pytest.mark.asyncio
async def test_publish_and_subscribe():
    bus = EventBus()
    results = []

    async def callback(msg: TagUpdateMsg):
        results.append(msg)

    bus.subscribe(TAG_UPDATE, callback)
    await bus.publish(TAG_UPDATE, TagUpdateMsg(tag_id="t1", value=42))
    await asyncio.sleep(0.01)
    assert results == [TagUpdateMsg(tag_id="t1", value=42)]

@pytest.mark.asyncio
async def test_multiple_subscribers():
    bus = EventBus()
    results1 = []
    results2 = []

    async def callback1(msg: TagUpdateMsg):
        results1.append(msg)

    async def callback2(msg: TagUpdateMsg):
        results2.append(msg)

    bus.subscribe(TAG_UPDATE, callback1)
    bus.subscribe(TAG_UPDATE, callback2)
    await bus.publish(TAG_UPDATE, TagUpdateMsg(tag_id="t2", value=123))
    await asyncio.sleep(0.01)
    assert results1 == [TagUpdateMsg(tag_id="t2", value=123)]
    assert results2 == [TagUpdateMsg(tag_id="t2", value=123)]

@pytest.mark.asyncio
async def test_unsubscribe():
    bus = EventBus()
    results = []

    async def callback(msg: TagUpdateMsg):
        results.append(msg)

    bus.subscribe(TAG_UPDATE, callback)
    bus.unsubscribe(TAG_UPDATE, callback)
    await bus.publish(TAG_UPDATE, TagUpdateMsg(tag_id="t3", value=999))
    await asyncio.sleep(0.01)
    assert results == []

@pytest.mark.asyncio
async def test_publish_no_subscribers():
    bus = EventBus()
    # Should not raise any error
    await bus.publish(TAG_UPDATE, TagUpdateMsg(tag_id="t4", value=True))
