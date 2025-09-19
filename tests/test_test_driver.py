import asyncio
import uuid
import pytest
from backend.communications.drivers.test.tank_test_driver import TankTestDriver
from openscada_lite.common.models.dtos import TagUpdateMsg, CommandFeedbackMsg
from openscada_lite.common.models.entities import Datapoint

import asyncio
import pytest

@pytest.mark.asyncio
async def test_test_driver_value_callback():
    driver = TankTestDriver("Server1")
    results = []
    event = asyncio.Event()

    def cb(msg: TagUpdateMsg):
        results.append(msg)
        event.set()  # signal that we got something
    
    driver.register_value_listener(cb)

    await driver.connect()
    driver.subscribe([Datapoint(name="TANK", type={"default": 0}),Datapoint(name="PUMP", type={"default": "CLOSED"}),Datapoint(name="DOOR", type={"default": "CLOSED"})])
    
    # Wait until callback fires (instead of blind sleep)
    await asyncio.sleep(2)

    await driver.disconnect()

    assert len(results) > 0
    assert results[0].datapoint_identifier == "Server1@TANK"


@pytest.mark.asyncio
async def test_test_driver_command_feedback():
    driver = TankTestDriver("Server1")
    feedback = []
    event = asyncio.Event()

    async def cb(msg: CommandFeedbackMsg):   # <-- async now
        feedback.append(msg)
        event.set()

    driver.register_command_feedback(cb)
    await driver.connect()
    await driver.send_command("TANK", 50, str(uuid.uuid4()))

    await asyncio.wait_for(event.wait(), timeout=2.0)
    await driver.disconnect()

    assert feedback[0].datapoint_identifier == "Server1@TANK"
    assert feedback[0].feedback == "OK"
    assert feedback[0].command_id is not None
