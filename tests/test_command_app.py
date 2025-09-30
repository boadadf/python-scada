import os

os.makedirs("svg", exist_ok=True)
os.environ["SCADA_CONFIG_PATH"] = "tests"

import asyncio
import pytest
import threading
import time
import socketio
import requests

from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.modules.command.service import CommandService
from openscada_lite.common.config.config import Config
from openscada_lite.common.models.dtos import CommandFeedbackMsg, SendCommandMsg
from openscada_lite.modules.command.model import CommandModel
from openscada_lite.app import app, socketio as flask_socketio

SERVER_URL = "http://localhost:5000"

@pytest.fixture(autouse=True)
def reset_event_bus(monkeypatch):
    # Reset the singleton before each test
    monkeypatch.setattr(EventBus, "_instance", None)

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

    # Send a command
    test_command = SendCommandMsg(
        command_id="testcmd1",
        datapoint_identifier="Server1@TANK",
        value=42,
    )
    response = requests.post(
        f"{SERVER_URL}/command_send_sendcommandmsg",
        json=test_command.to_dict()
    )
    assert response.status_code == 200

    assert received_feedback, "No command feedback received after sending command"
    feedback = received_feedback[-1]
    assert feedback["command_id"] == "testcmd1"
    assert feedback["datapoint_identifier"] == "Server1@TANK"
    # Optionally check feedback['feedback'] or other fields

    sio.disconnect()

def test_command_model_initial_load(monkeypatch):
    # Mock Config.get_instance().get_allowed_command_identifiers()
    allowed = ["Server1@CMD1", "Server2@CMD2"]
    class DummyConfig:
        def get_allowed_command_identifiers(self):
            return allowed
    monkeypatch.setattr(Config, "get_instance", lambda: DummyConfig())

    model = CommandModel()
    # The model should have all allowed commands in its _store
    for cmd_id in allowed:
        assert cmd_id in model._store
        feedback = model._store[cmd_id]
        assert feedback.datapoint_identifier == cmd_id
        assert feedback.feedback is None    

@pytest.mark.asyncio
async def test_command_service_handle_bus_message(monkeypatch):
    allowed = ["Server1@CMD1"]
    class DummyConfig:
        def get_allowed_command_identifiers(self):
            return allowed
    monkeypatch.setattr(Config, "get_instance", lambda: DummyConfig())

    bus = EventBus.get_instance()
    model = CommandModel()
    service = CommandService(bus, model, controller=None)

    msg = CommandFeedbackMsg(
        command_id="cmd123",
        datapoint_identifier="Server1@CMD1",
        value=42,
        feedback="OK",
        timestamp=None
    )

    await service.handle_bus_message(msg)

    stored = model._store.get("Server1@CMD1")
    assert stored is not None
    assert stored.command_id == "cmd123"
    assert stored.value == 42
    assert stored.feedback == "OK"