import asyncio
import pytest
from core.communications.drivers.test.tank_test_driver import TankTestDriver
from openscada_lite.common.models.dtos import SendCommandMsg, TagUpdateMsg, CommandFeedbackMsg
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
    driver.subscribe([Datapoint(name="TANK", type={"default": 0}),Datapoint(name="PUMP", type={"default": "CLOSED"}),Datapoint(name="DOOR", type={"default": "CLOSED"})])

    await driver.connect()
    
    
    # Wait until callback fires (instead of blind sleep)
    await asyncio.sleep(2)

    await driver.disconnect()

    assert len(results) > 0
    assert results[0].datapoint_identifier == "Server1@TANK"


@pytest.mark.asyncio
async def test_test_driver_command_feedback():
    driver = TankTestDriver("Server1")
    # Create the datapoint and subscribe
    dp = Datapoint(name="TANK", type={"type": "float", "default": 0.0})
    driver.subscribe([dp])

    feedback = []
    event = asyncio.Event()

    async def cb(msg):
        feedback.append(msg)
        event.set()

    driver.register_command_feedback(cb)
    await driver.connect()
    await driver.send_command(SendCommandMsg("cmd1", "Server1@TANK", 50 ))
    await asyncio.wait_for(event.wait(), timeout=2.0)
    await driver.disconnect()

    assert feedback[0].datapoint_identifier == "Server1@TANK"
    assert feedback[0].feedback == "OK"