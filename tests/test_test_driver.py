import asyncio
import uuid
import pytest
from backend.communications.drivers.test_driver import TestDriver
from app.common.models.dtos import TagUpdateMsg, CommandFeedbackMsg
from common.models.entities import Datapoint

@pytest.mark.asyncio
async def test_test_driver_value_callback():
    driver = TestDriver("Server1")
    results = []
    async def cb(msg: TagUpdateMsg):
        results.append(msg)
    driver.register_value_listener(cb)

    await driver.connect()
    driver.subscribe([Datapoint(name="TANK1_LEVEL", type={"default": 0})])
    
    # Let it publish once
    await asyncio.sleep(1.1)

    await driver.disconnect()
    assert len(results) > 0
    assert results[0].datapoint_identifier == "Server1@TANK1_LEVEL"

@pytest.mark.asyncio
async def test_test_driver_command_feedback():
    driver = TestDriver("Server1")
    feedback = []

    async def cb(msg: CommandFeedbackMsg):
        feedback.append(msg)

    driver.register_command_feedback(cb)
    await driver.connect()
    await driver.send_command("TANK1_LEVEL", 50, uuid.uuid4())

    await asyncio.sleep(0.1)
    await driver.disconnect()

    assert feedback[0].datapoint_identifier == "Server1@TANK1_LEVEL"
    assert feedback[0].status == "OK"
    assert feedback[0].command_id is not None
