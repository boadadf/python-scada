from asyncio import sleep
import pytest
import datetime
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import APIRouter, FastAPI
from openscada_lite.common.models.dtos import TagUpdateMsg
from openscada_lite.common.config.config import Config
from openscada_lite.modules.datapoint.model import DatapointModel
from openscada_lite.modules.datapoint.controller import DatapointController


@pytest.fixture(autouse=True)
def reset_config_singleton():
    Config.reset_instance()
    Config.get_instance("tests/test_config.json")


def setup_function():
    Config.reset_instance()


@pytest.fixture
def model():
    m = DatapointModel()
    # Add a test tag for initial state
    m._store["Test@TAG"] = TagUpdateMsg(
        datapoint_identifier="Test@TAG",
        value=123,
        quality="good",
        timestamp="2025-09-15T12:00:00Z",
    )
    return m


@pytest.fixture
def socketio_mock():
    sio = MagicMock()
    sio.join_room = AsyncMock()
    sio.emit = AsyncMock()
    return sio


@pytest.fixture
def controller(model, socketio_mock):
    module_name = "datapoint"
    router = APIRouter()

    # Create the DatapointController instance
    controller = DatapointController(model, socketio_mock, module_name, router)
    controller.register_socketio()  # Ensure events are registered
    return controller


def test_publish_tag_blocks_when_initializing(controller):
    controller._initializing_clients.add("sid1")
    controller.socketio.emit.reset_mock()
    controller.publish(
        TagUpdateMsg(
            datapoint_identifier="Test@TAG",
            value=456,
            quality="good",
            timestamp=datetime.datetime.now(),
        )
    )
    controller.socketio.emit.assert_not_called()


@pytest.mark.asyncio
async def test_publish_tag_emits_when_no_initializing(controller):
    controller.socketio.emit.reset_mock()  # Ensure clean state

    # Publish a message
    controller.publish(
        TagUpdateMsg(
            datapoint_identifier="Test@TAG",
            value=456,
            quality="good",
            timestamp=datetime.datetime.now(),
        )
    )

    # Wait for the batch worker to process the buffer
    await sleep(1.1)  # Slightly longer than the batch interval (1 second)

    # Assert that socketio.emit was called
    controller.socketio.emit.assert_called_once()
    args, kwargs = controller.socketio.emit.call_args
    assert args[0] == "datapoint_tagupdatemsg"
    assert any(tag["datapoint_identifier"] == "Test@TAG" and tag["value"] == 456 for tag in args[1])


@pytest.mark.asyncio
async def test_handle_subscribe_live_feed_emits_initial_state(controller):
    # Mock the `enter_room` method
    with patch.object(controller.socketio, "enter_room", new_callable=AsyncMock) as mock_enter_room:
        # Mock the `trigger_event` method
        async def mock_trigger_event(event_name, *args, **kwargs):
            if event_name == f"{controller.base_event}_subscribe_live_feed":
                await controller.handle_subscribe_live_feed(*args, **kwargs)

        controller.socketio.trigger_event = mock_trigger_event
        controller.socketio.emit.reset_mock()

        # Trigger the event
        event_name = f"{controller.base_event}_subscribe_live_feed"
        await controller.socketio.trigger_event(event_name, "sid1")

        # Assert that `enter_room` was called with the correct room
        mock_enter_room.assert_called_once_with("sid1", "datapoint_room")

        # Verify that the initial state was emitted
        found = False
        for call_args in controller.socketio.emit.call_args_list:
            if call_args[0][0] == "datapoint_initial_state":
                tag_list = call_args[0][1]
                # Check that the test tag is in the list
                assert any(
                    tag["datapoint_identifier"] == "Test@TAG" and tag["value"] == 123
                    for tag in tag_list
                )
                found = True
        assert found, "No initial_state emit found"


@pytest.mark.asyncio
async def test_set_tag_calls_service_and_emits_ack(controller):
    from openscada_lite.modules.datapoint.controller import DatapointController
    import json
    import datetime
    from unittest.mock import AsyncMock, MagicMock
    from openscada_lite.common.models.dtos import (
        RawTagUpdateMsg,
    )

    # Create the FastAPI app and include the controller's router
    app = FastAPI()
    router = APIRouter()
    controller = DatapointController(MagicMock(), MagicMock(), "datapoint", router)
    controller.service = MagicMock()
    controller.service.handle_controller_message = AsyncMock(return_value=True)
    app.include_router(router)

    # Create test data
    now = datetime.datetime.now()
    test_data = RawTagUpdateMsg(
        track_id="1234",
        datapoint_identifier="Test@TAG",
        value=42,
        quality="good",
        timestamp=now,
    )

    # Use FastAPI's TestClient to simulate requests
    client = TestClient(app)
    response = client.post(
        "/datapoint_send_rawtagupdatemsg",
        content=json.dumps(test_data.to_dict()),  # Use 'content' instead of 'data'
        headers={"Content-Type": "application/json"},
    )

    # Assert the response
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "reason": "Request accepted."}

    # Verify that the service's handle_controller_message method was called
    expected_data = RawTagUpdateMsg(
        track_id="1234",
        datapoint_identifier="Test@TAG",
        value=42,
        quality="good",
        timestamp=test_data.timestamp.isoformat(),  # Expect string, not datetime
    )
    controller.service.handle_controller_message.assert_called_once_with(expected_data)
