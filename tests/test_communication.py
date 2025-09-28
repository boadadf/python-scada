from flask import Flask
import json
import asyncio
from typing import Any
import pytest
from unittest.mock import ANY, AsyncMock, MagicMock, patch
from openscada_lite.common.models.dtos import DriverConnectCommand, DriverConnectStatus, RawTagUpdateMsg, StatusDTO
from openscada_lite.modules.communication.controller import CommunicationController
from openscada_lite.modules.communication.service import CommunicationService
from openscada_lite.modules.communication.model import CommunicationModel
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.core.communications.connector_manager import ConnectorManager
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.config.config import Config

#Reset the bus for each test
@pytest.fixture(autouse=True)
def reset_event_bus(monkeypatch):
    # Reset the singleton before each test
    monkeypatch.setattr(EventBus, "_instance", None)

class DummyEventBus(EventBus):
    def __init__(self):
        super().__init__()
        self.published = []

    async def publish(self, event_type, data):
        self.published.append((event_type, data))

@pytest.fixture
def controller():
    model = MagicMock()
    socketio = MagicMock()
    ctrl = CommunicationController(model, socketio)
    service = MagicMock()
    ctrl.service = service
    return ctrl

@pytest.fixture
def service():
    from unittest.mock import AsyncMock
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()
    model = MagicMock()
    controller = MagicMock()
    svc = CommunicationService(event_bus, model, controller)
    return svc, event_bus, model

def test_handle_connect_driver_valid_status():
    from openscada_lite.modules.communication.controller import CommunicationController
    from flask import Flask
    import json

    app = Flask(__name__)
    controller = CommunicationController(MagicMock(), MagicMock(), flask_app=app)
    # Set service to a MagicMock so you can assert calls
    controller.service = MagicMock()
    controller.service.handle_controller_message = AsyncMock(return_value=True)
    data = DriverConnectCommand(driver_name="Server1", status="connect")

    with app.test_client() as client, app.app_context():
        response = client.post(
            "/communication_send_driverconnectcommand",
            data=json.dumps(data.to_dict()),
            content_type="application/json"
        )
        assert response.status_code == 200
        assert response.get_json() == {"status": "ok", "reason": "Request accepted."}

    # Check service and emit calls
    controller.service.handle_controller_message.assert_called_once_with(data)

def test_handle_connect_driver_invalid_status():
    from openscada_lite.modules.communication.controller import CommunicationController
    from flask import Flask
    import json

    app = Flask(__name__)
    controller = CommunicationController(MagicMock(), MagicMock(), flask_app=app)
    controller.service = MagicMock()
    controller.service.handle_controller_message = AsyncMock(return_value=True)
    data = DriverConnectCommand(driver_name="Server1", status="bad_status")

    with app.test_client() as client, app.app_context():
        response = client.post(
            "/communication_send_driverconnectcommand",
            data=json.dumps(data.to_dict()),
            content_type="application/json"
        )
        assert response.status_code == 400
        assert response.get_json() == {
            "status": "error",
            "reason": "Invalid status. Must be 'connect' or 'disconnect'."
        }

    controller.service.handle_controller_message.assert_not_called()
@pytest.mark.asyncio
async def test_handle_subscribe_driver_status(controller):
    controller.socketio.emit = MagicMock()
    controller.socketio.join_room = MagicMock()
    controller.model.get_all_status.return_value = {"Server1": "connect"}
    sid = "sid123"

    handlers = {}
    def fake_on(event):
        def decorator(fn):
            handlers[event] = fn
            return fn
        return decorator
    controller.socketio.on = fake_on
    controller.socketio.sid = sid
    controller.register_socketio()

    with patch("openscada_lite.modules.base.base_controller.join_room", MagicMock()):
        handlers["communication_subscribe_live_feed"]()

    controller.socketio.emit.assert_any_call(
        "communication_initial_state",
        [v.to_dict() for v in controller.model.get_all().values()],
        room="communication_room"
    )

def test_publish_status(controller):
    controller.socketio.emit = MagicMock()
    controller.publish(DriverConnectCommand(track_id="1234", driver_name="Server1", status="connect"))
    controller.socketio.emit.assert_called_once_with(
        "communication_driverconnectstatus",
        {"track_id": "1234", "driver_name": "Server1", "status": "connect"},
        room="communication_room"
    )

@pytest.mark.asyncio
async def test_send_connect_command_publishes_event(service):
    svc, event_bus, _ = service
    await svc.handle_controller_message(DriverConnectCommand("Server1", "connect"))
    event_bus.publish.assert_called_once_with(
        EventType.DRIVER_CONNECT_COMMAND,
        DriverConnectCommand(track_id=ANY, driver_name="Server1", status="connect")
    )

@pytest.mark.asyncio
async def test_on_driver_connect_status_updates_model_and_notifies_controller(service):
    svc, _, model = service
    svc.controller = MagicMock()
    data = DriverConnectStatus(track_id="1234", driver_name="Server1", status="connect")
    await svc.handle_bus_message(data)
    model.update.assert_called_once_with(DriverConnectStatus(track_id="1234", driver_name="Server1", status="connect"))
    svc.controller.publish.assert_called_once_with(DriverConnectStatus(track_id="1234", driver_name="Server1", status="connect"))

def test_set_and_get_status():
    model = CommunicationModel()
    model.update(DriverConnectStatus("Server1", "connect"))
    model.update(DriverConnectStatus("Server2", "disconnect"))
    # Compare the status values, not the DTO objects
    assert {k: v.status for k, v in model.get_all().items()} == {"Server1": "connect", "Server2": "disconnect"}
    # Changing the returned dict does not affect the model
    all_status = model.get_all()
    all_status["Server1"].status = "disconnect"
    assert model.get_all()["Server1"].status == "connect"

def test_driver_initial_status_is_disconnected():
    """
    When a driver is started, it should always send a status event that it's 'disconnect'.
    """
    from openscada_lite.modules.communication.model import CommunicationModel

    model = CommunicationModel()
    # Simulate driver startup
    driver_name = "Server1"
    # On startup, the driver should set its status to 'disconnect'
    model.update(DriverConnectStatus(driver_name, "disconnect"))
    assert model.get_all()[driver_name].status == "disconnect"

@pytest.mark.asyncio
async def test_driver_publishes_disconnected_status_on_start():
    """
    When a driver is started, it should publish a status event with 'disconnect'.
    """
    # Reset config singleton and load test config
    Config.reset_instance()
    Config.get_instance("tests/test_config.json")

    bus = EventBus.get_instance()
    connector_manager = ConnectorManager(bus)

    status_events = []
    waitEvent = asyncio.Event()

    async def status_handler(event):
        status_events.append(event)
        waitEvent.set()  # signal that we got something
    # Subscribe to DRIVER_STATUS events
    bus.subscribe(EventType.DRIVER_CONNECT_STATUS, status_handler)

    await connector_manager.start_all()
    # Give some time for status events to be published
    await asyncio.wait_for(waitEvent.wait(), timeout=2.0)

    # There should be at least one status event with 'offline'
    assert any(
        getattr(event, "status", None) == "offline"
        for event in status_events
    ), f"No 'offline' status event found in: {status_events}"

    await connector_manager.stop_all()

def test_emit_communication_status_sets_unknown(monkeypatch):
    class DummyConfig:
        def get_datapoint_types_for_driver(self, driver_name, types):
            if driver_name == "TestDriver":
                return {
                    "TANK": {"default": 0.0},
                    "PUMP": {"default": "CLOSED"}
                }
            return {}
        def get_drivers(self): return []
        def get_types(self): return {}

    monkeypatch.setattr("openscada_lite.common.config.config.Config.get_instance", lambda: DummyConfig())

    # Set the EventBus singleton to DummyEventBus
    from openscada_lite.common.bus.event_bus import EventBus
    EventBus._instance = DummyEventBus()

    bus = EventBus.get_instance()
    manager = ConnectorManager(bus)
    manager.driver_status["TestDriver"] = "online"
    status = DriverConnectStatus(driver_name="TestDriver", status="offline")
    import asyncio
    asyncio.run(manager.emit_communication_status(status))

    raw_updates = [d for e, d in bus.published if e == EventType.RAW_TAG_UPDATE]
    assert len(raw_updates) == 2
    for msg in raw_updates:
        assert isinstance(msg, RawTagUpdateMsg)
        assert msg.quality == "unknown"
        assert msg.datapoint_identifier in ["TestDriver@TANK", "TestDriver@PUMP"]
        if msg.datapoint_identifier.endswith("TANK"):
            assert msg.value == 0.0
        elif msg.datapoint_identifier.endswith("PUMP"):
            assert msg.value == "CLOSED"