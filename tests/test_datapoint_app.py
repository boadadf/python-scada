import os
os.environ["SCADA_CONFIG_PATH"] = "tests"


import asyncio
import pytest
import threading
import time
import socketio
from openscada_lite.app import app, socketio as flask_socketio
from common.models.dtos import RawTagUpdateMsg
import requests

SERVER_URL = "http://localhost:5000"

@pytest.fixture(autouse=True)
def ensure_svg_folder_exists():
    svg_dir = os.path.abspath("config/svg")
    if not os.path.exists(svg_dir):
        os.makedirs(svg_dir)

@pytest.fixture(scope="module", autouse=True)
def run_server():
    # Start the Flask app in a background thread
    thread = threading.Thread(
       target=lambda: flask_socketio.run(app, port=5000, allow_unsafe_werkzeug=True),
       daemon=True
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
async def test_live_feed_and_set_tag_real():
    # Connect to the live feed using a real SocketIO client
    sio = socketio.Client()
    received_initial = []
    received_updates = []

    @sio.on('datapoint_initial_state')
    def on_initial_state(data):
        received_initial.append(data)

    @sio.on('datapoint_tagupdatemsg')
    def on_datapoint_update(data):
        received_updates.append(data)

    sio.connect(SERVER_URL)
    sio.emit('datapoint_subscribe_live_feed')
    await asyncio.sleep(1)  # Wait for initial state

    # Check initial state contains all tags from test_config.json
    import json, os
    with open(os.path.join(os.path.dirname(__file__), "test_config.json")) as f:
        config = json.load(f)

    expected_tags = []
    for driver in config["drivers"]:
        for dp in driver["datapoints"]:
            expected_tags.append(f"{driver['name']}@{dp['name']}")

    assert received_initial, "No initial_state received"
    initial_tags = {dp['datapoint_identifier'] for dp in received_initial[0]}
    for tag in expected_tags:
        assert tag in initial_tags

    # Set a value for one tag using HTTP POST (if you have a REST endpoint), or via WebSocket
    test_tag = expected_tags[0]
    test_value = 123.45
    requests.post(
        f"{SERVER_URL}/datapoint_send_rawtagupdatemsg",
        json=RawTagUpdateMsg(test_tag, test_value, "good", None).to_dict()
    )
    await asyncio.sleep(1)  # Wait for update

    assert received_updates, "No datapoint_update received after set_tag"
    update = received_updates[-1]
    assert update['datapoint_identifier'] == test_tag
    assert update['value'] == test_value

    sio.disconnect()