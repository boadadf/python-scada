import pytest
import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from openscada_lite.common.models.dtos import RawTagUpdateMsg, StatusDTO, TagUpdateMsg
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
    m._store["Test@TAG"] = TagUpdateMsg(datapoint_identifier="Test@TAG", value=123, quality="good", timestamp="2025-09-15T12:00:00Z")
    return m

@pytest.fixture
def controller(model):
    mock_socketio = MagicMock()
    return DatapointController(model, mock_socketio)    

def test_publish_tag_blocks_when_initializing(controller):
    controller._initializing_clients.add("sid1")
    controller.socketio.emit.reset_mock()
    controller.publish(TagUpdateMsg(datapoint_identifier="Test@TAG", value=456, quality="good", timestamp=datetime.datetime.now()))
    controller.socketio.emit.assert_not_called()

@pytest.mark.asyncio
async def test_publish_tag_emits_when_no_initializing(controller):
    controller.socketio.emit.reset_mock()  # Ensure clean state
    controller.publish(TagUpdateMsg(datapoint_identifier="Test@TAG", value=456, quality="good", timestamp=datetime.datetime.now()))
    controller.socketio.emit.assert_called_once()
    args, kwargs = controller.socketio.emit.call_args
    assert args[0] == "datapoint_tagupdatemsg"
    assert args[1]["datapoint_identifier"] == "Test@TAG"

def test_handle_subscribe_live_feed_emits_initial_state(controller):
    with patch("openscada_lite.modules.base.base_controller.join_room") as mock_join_room:
        controller.socketio.emit.reset_mock()
        controller.handle_subscribe_live_feed()
        mock_join_room.assert_called_once_with("datapoint_room")
        # Get the actual call arguments
        found = False
        for call_args in controller.socketio.emit.call_args_list:
            if call_args[0][0] == "datapoint_initial_state":
                tag_list = call_args[0][1]
                # Check that your test tag is in the list
                assert any(tag["datapoint_identifier"] == "Test@TAG" and tag["value"] == 123 for tag in tag_list)
                found = True
        assert found, "No initial_state emit found"
        
def test_set_tag_calls_service_and_emits_ack():
    from openscada_lite.modules.datapoint.controller import DatapointController
    from flask import Flask
    import json
    import datetime
    from unittest.mock import AsyncMock, MagicMock
    from openscada_lite.common.models.dtos import RawTagUpdateMsg, StatusDTO, TagUpdateMsg

    app = Flask(__name__)
    model = DatapointModel()
    controller = DatapointController(model, MagicMock(), flask_app=app)
    controller.service = MagicMock()
    controller.service.handle_controller_message = AsyncMock(return_value=True)

    now = datetime.datetime.now()
    test_data = RawTagUpdateMsg(track_id="1234", datapoint_identifier="Test@TAG", value=42, quality="good", timestamp=now)

    with app.test_client() as client, app.app_context():
        response = client.post(
            "/datapoint_send_rawtagupdatemsg",
            data=json.dumps(test_data.to_dict()),
            content_type="application/json"
        )
        assert response.status_code == 200
        assert response.get_json() == {"status": "ok", "reason": "Request accepted."}

    expected_data = RawTagUpdateMsg(
        track_id="1234",
        datapoint_identifier="Test@TAG",
        value=42,
        quality="good",
        timestamp=test_data.timestamp.isoformat()  # Expect string, not datetime
    )
    controller.service.handle_controller_message.assert_called_once_with(expected_data)