import os
os.environ["SCADA_CONFIG_FILE"] = "tests/test_config.json"

import pytest
import threading
import time
import requests
import socketio
from app import app, socketio as flask_socketio
from common.config.config import Config

SERVER_URL = "http://localhost:5000"

@pytest.fixture(scope="module", autouse=True)
def run_server():
    # Start the Flask app in a background thread
    thread = threading.Thread(
       target=lambda: flask_socketio.run(app, port=5000, allow_unsafe_werkzeug=True),
       daemon=True
    )
    thread.start()
    time.sleep(1)  # Give the server time to start
    yield
    # No explicit shutdown; daemon thread will exit with pytest

def test_live_feed_and_set_tag_real():
    # Connect to the live feed using a real SocketIO client
    sio = socketio.Client()
    received_initial = []
    received_updates = []

    @sio.on('initial_state')
    def on_initial_state(data):
        received_initial.append(data)

    @sio.on('datapoint_update')
    def on_datapoint_update(data):
        received_updates.append(data)

    sio.connect(SERVER_URL)
    sio.emit('subscribe_live_feed')
    time.sleep(1)  # Wait for initial state

    # Check initial state contains all tags from test_config.json
    import json, os
    with open(os.path.join(os.path.dirname(__file__), "test_config.json")) as f:
        config = json.load(f)
    expected_tags = []
    for driver in config["drivers"]:
        for dp in driver["datapoints"]:
            expected_tags.append(f"{driver['name']}@{dp}")

    assert received_initial, "No initial_state received"
    initial_tags = {dp['datapoint_identifier'] for dp in received_initial[0]}
    for tag in expected_tags:
        assert tag in initial_tags

    # Set a value for one tag using HTTP POST (if you have a REST endpoint), or via WebSocket
    test_tag = expected_tags[0]
    test_value = 123.45
    sio.emit('set_tag', {"datapoint_identifier": test_tag, "value": test_value, "quality": "good"})
    time.sleep(1)  # Wait for update

    assert received_updates, "No datapoint_update received after set_tag"
    update = received_updates[-1]
    assert update['datapoint_identifier'] == test_tag
    assert update['value'] == test_value

    sio.disconnect()