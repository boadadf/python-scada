import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.common.models.dtos import TagUpdateMsg
from app.common.config.config import Config
from app.frontend.datapoints.model import DatapointModel
from app.frontend.datapoints.controller import DatapointController

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
    m._tags["Test@TAG"] = TagUpdateMsg(datapoint_identifier="Test@TAG", value=123, quality="good", timestamp="2025-09-15T12:00:00Z")
    return m

@pytest.fixture
def controller(model):
    mock_socketio = MagicMock()
    return DatapointController(model, mock_socketio)    

def test_publish_tag_blocks_when_initializing(controller):
    controller._initializing_clients.add("sid1")
    controller.socketio.emit.reset_mock()
    controller.publish_tag(TagUpdateMsg(datapoint_identifier="Test@TAG", value=456, quality="good", timestamp="2025-09-15T12:01:00Z"))
    controller.socketio.emit.assert_not_called()

def test_publish_tag_emits_when_no_initializing(controller):
    controller.socketio.emit.reset_mock()  # Ensure clean state
    controller.publish_tag(TagUpdateMsg(datapoint_identifier="Test@TAG", value=456, quality="good", timestamp="2025-09-15T12:01:00Z"))
    controller.socketio.emit.assert_called_once()
    args, kwargs = controller.socketio.emit.call_args
    assert args[0] == "datapoint_update"
    assert args[1]["datapoint_identifier"] == "Test@TAG"

def test_handle_subscribe_live_feed_emits_initial_state(controller):
    with patch("app.frontend.datapoints.controller.join_room") as mock_join_room:
        controller.socketio.emit.reset_mock()
        controller.handle_subscribe_live_feed()
        mock_join_room.assert_called_once_with("datapoint_live_feed")
        # Get the actual call arguments
        found = False
        for call_args in controller.socketio.emit.call_args_list:
            if call_args[0][0] == "initial_state":
                tag_list = call_args[0][1]
                # Check that your test tag is in the list
                assert any(tag["datapoint_identifier"] == "Test@TAG" and tag["value"] == 123 for tag in tag_list)
                found = True
        assert found, "No initial_state emit found"
        
def test_set_tag_calls_service_and_emits_ack(controller):
    controller.service = MagicMock()
    controller.service.update_tag = AsyncMock(return_value=True)

    def immediate_call(func, *args, **kwargs):
        func(*args, **kwargs)
    controller.socketio.start_background_task.side_effect = immediate_call

    test_data = {"datapoint_identifier": "Test@TAG", "value": 42, "quality": "good", "timestamp": "2025-09-15T12:00:00Z"}
    controller.handle_set_tag(test_data)

    controller.service.update_tag.assert_called_once_with("Test@TAG", 42, "good", "2025-09-15T12:00:00Z")
    controller.socketio.emit.assert_any_call('set_tag_ack', {"status": "ok", "datapoint_identifier": "Test@TAG"})