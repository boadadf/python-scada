import os
import json

import asyncio
import pytest
import socketio
import aiofiles
from openscada_lite.common.models.dtos import RawTagUpdateMsg
import requests
from openscada_lite.common.utils import SecurityUtils

SERVER_URL = "http://localhost:5001"


@pytest.fixture(scope="session", autouse=True)
def run_server():
    import subprocess
    import time
    import os

    # Ensure SCADA_CONFIG_PATH is set
    os.environ["SCADA_CONFIG_PATH"] = "tests/config/test_config.json"

    # Start Uvicorn in a subprocess
    process = subprocess.Popen(
        [
            "uvicorn",
            "openscada_lite.app:asgi_app",
            "--host",
            "127.0.0.1",
            "--port",
            "5001",
        ],
        env=os.environ.copy(),  # Pass the current environment variables to the subprocess
    )
    time.sleep(2)  # Give the server time to start
    yield
    process.terminate()
    process.wait()


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

    @sio.on("datapoint_initial_state")
    def on_initial_state(data):
        received_initial.append(data)

    @sio.on("datapoint_tagupdatemsg")
    def on_datapoint_update(data):
        received_updates.append(data)

    # Connect to the server
    sio.connect(SERVER_URL)  # Ensure the client connects to the server

    # Emit the subscription event
    sio.emit("datapoint_subscribe_live_feed")
    await asyncio.sleep(1)  # Wait for initial state

    async with aiofiles.open(
        os.path.join(os.path.dirname(__file__), "config", "test_config.json")
    ) as f:
        content = await f.read()
        config = json.loads(content)

    expected_tags = []
    for driver in config["drivers"]:
        for dp in driver["datapoints"]:
            expected_tags.append(f"{driver['name']}@{dp['name']}")

    assert received_initial, "No initial_state received"
    initial_tags = {dp["datapoint_identifier"] for dp in received_initial[0]}
    for tag in expected_tags:
        assert tag in initial_tags
    token = SecurityUtils.create_jwt("admin", "test_group")
    headers = {"Authorization": f"Bearer {token}"}

    # Set a value for one tag using HTTP POST (if you have a REST endpoint), or via WebSocket
    test_tag = expected_tags[0]
    test_value = 123.45
    requests.post(
        f"{SERVER_URL}/datapoint_send_rawtagupdatemsg",
        json=RawTagUpdateMsg(test_tag, test_value, "good", None).to_dict(),
        headers=headers,
    )
    await asyncio.sleep(1.1)  # Wait for update

    assert received_updates, "No datapoint_update received after set_tag"

    # Flatten the received updates (in case of batched messages)
    all_updates = [item for batch in received_updates for item in batch]

    # Check if the expected update is in the batch
    update = next((u for u in all_updates if u["datapoint_identifier"] == test_tag), None)
    assert update is not None, "Expected update not found in received updates"
    assert update["value"] == pytest.approx(test_value)

    sio.disconnect()
