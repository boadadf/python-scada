import asyncio
import os

from backend.communications.drivers.test.test_driver import TestDriver
from common.models.dtos import SendCommandMsg
from openscada_lite.common.models.entities import Datapoint

os.environ["SCADA_CONFIG_FILE"] = "tests/test_config.json"

import pytest
import threading
import time
import socketio
from openscada_lite.app import app, socketio as flask_socketio

SERVER_URL = "http://localhost:5000"


@pytest.fixture(scope="module", autouse=True)
def run_server():
    # Start the Flask app in a background thread
    thread = threading.Thread(
        target=lambda: flask_socketio.run(
            app, port=5000, allow_unsafe_werkzeug=True
        ),
        daemon=True,
    )
    flask_socketio.start_background_task = immediate_call
    thread.start()
    time.sleep(1)  # Give the server time to start
    yield
    # No explicit shutdown; daemon thread will exit with pytest


def immediate_call(func, *args, **kwargs):
    import asyncio

    if asyncio.iscoroutinefunction(func):
        asyncio.run(func(*args, **kwargs))
    else:
        func(*args, **kwargs)


@pytest.mark.asyncio
async def test_command_live_feed_and_feedback():
    sio = socketio.Client()
    received_initial = []
    received_feedback = []

    @sio.on("command_initial_state")
    def on_initial_state(data):
        received_initial.append(data)

    @sio.on("command_commandfeedbackmsg")
    def on_command_feedback(data):
        received_feedback.append(data)

    sio.connect(SERVER_URL)
    sio.emit("command_subscribe_live_feed")
    await asyncio.sleep(1)  # Wait for initial state

    # Optionally check initial state
    assert received_initial is not None

    # Send a command (adjust fields as needed)
    test_command = SendCommandMsg(
        command_id="testcmd1",
        datapoint_identifier="Server1@TANK",
        value=42,
    )
    sio.emit("command_send_sendcommandmsg", test_command.to_dict())
    await asyncio.sleep(5)  # Wait for initial state

    assert received_feedback, "No command feedback received after sending command"
    feedback = received_feedback[-1]
    assert feedback["command_id"] == "testcmd1"
    assert feedback["datapoint_identifier"] == "Server1@TANK"
    # Optionally check feedback['feedback'] or other fields

    sio.disconnect()