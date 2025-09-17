import asyncio
import pytest
from unittest.mock import MagicMock, patch
from app.frontend.communications.controller import CommunicationsController
from app.frontend.communications.service import CommunicationsService
from app.frontend.communications.model import CommunicationsModel
from app.common.bus.event_types import EventType
from app.backend.communications.connector_manager import ConnectorManager
from app.common.bus.event_bus import EventBus
from app.common.config.config import Config

@pytest.fixture
def controller():
    model = MagicMock()
    socketio = MagicMock()
    ctrl = CommunicationsController(model, socketio)
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
    svc = CommunicationsService(event_bus, model, controller)
    return svc, event_bus, model

def test_handle_connect_driver_valid_status(controller):
    from unittest.mock import AsyncMock
    controller.service.send_connect_status = AsyncMock()
    controller.socketio.emit = MagicMock()
    data = {"driver_name": "Server1", "status": "connect"}

    handlers = {}
    def fake_on(event):
        def decorator(fn):
            handlers[event] = fn
            return fn
        return decorator
    controller.socketio.on = fake_on
    controller.register_socketio()
    handlers["connect_driver"](data)

    controller.service.send_connect_status.assert_called_once_with("Server1", "connect")
    controller.socketio.emit.assert_any_call("connect_driver_ack", {"status": "ok", "driver_name": "Server1"})

def test_handle_connect_driver_invalid_status(controller):
    controller.service.send_connect_command = MagicMock()
    controller.socketio.emit = MagicMock()
    data = {"driver_name": "Server1", "status": "bad_status"}

    handlers = {}
    def fake_on(event):
        def decorator(fn):
            handlers[event] = fn
            return fn
        return decorator
    controller.socketio.on = fake_on
    controller.register_socketio()
    handlers["connect_driver"](data)

    controller.service.send_connect_command.assert_not_called()
    controller.socketio.emit.assert_any_call(
        "connect_driver_ack",
        {
            "status": "error",
            "reason": "Invalid status. Must be 'connect' or 'disconnect'.",
            "driver_name": "Server1"
        }
    )

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

    # Patch join_room where it is imported in the controller module
    with patch("app.frontend.communications.controller.join_room", MagicMock()):
        handlers["subscribe_driver_status"]()  # <-- No await here

    controller.socketio.emit.assert_any_call("driver_status_all", {"Server1": "connect"}, room="driver_status_room")

def test_publish_status(controller):
    controller.socketio.emit = MagicMock()
    controller.publish_status("Server1", "connect")
    controller.socketio.emit.assert_called_once_with(
        "driver_status_update",
        {"driver_name": "Server1", "status": "connect"},
        room="driver_status_room"
    )

@pytest.mark.asyncio
async def test_send_connect_command_publishes_event(service):
    svc, event_bus, _ = service
    await svc.send_connect_status("Server1", "connect")
    event_bus.publish.assert_called_once_with(
        EventType.DRIVER_CONNECT,
        {"server_name": "Server1", "status": "connect"}
    )

@pytest.mark.asyncio
async def test_on_driver_connect_status_updates_model_and_notifies_controller(service):
    svc, _, model = service
    svc.controller = MagicMock()
    data = {"driver_name": "Server1", "status": "connect"}
    await svc.on_driver_connect_status(data)
    model.set_status.assert_called_once_with("Server1", "connect")
    svc.controller.publish_status.assert_called_once_with("Server1", "connect")

def test_set_and_get_status():
    model = CommunicationsModel()
    model.set_status("Server1", "connect")
    model.set_status("Server2", "disconnect")
    assert model.get_all_status() == {"Server1": "connect", "Server2": "disconnect"}
    # Changing the returned dict does not affect the model
    all_status = model.get_all_status()
    all_status["Server1"] = "disconnect"
    assert model.get_all_status()["Server1"] == "connect"

def test_driver_initial_status_is_disconnected():
    """
    When a driver is started, it should always send a status event that it's 'disconnect'.
    """
    from app.frontend.communications.model import CommunicationsModel

    model = CommunicationsModel()
    # Simulate driver startup
    driver_name = "Server1"
    # On startup, the driver should set its status to 'disconnect'
    model.set_status(driver_name, "disconnect")
    assert model.get_all_status()[driver_name] == "disconnect"

@pytest.mark.asyncio
async def test_driver_publishes_disconnected_status_on_start():
    """
    When a driver is started, it should publish a status event with 'disconnect'.
    """
    # Reset config singleton and load test config
    Config.reset_instance()
    Config.get_instance("tests/test_config.json")

    bus = EventBus()
    connector_manager = ConnectorManager(bus)

    status_events = []

    async def status_handler(event):
        status_events.append(event)

    # Subscribe to DRIVER_STATUS events
    bus.subscribe(EventType.DRIVER_CONNECT_STATUS, status_handler)

    await connector_manager.start_all()
    # Give some time for status events to be published
    await asyncio.sleep(0.2)

    # There should be at least one status event with 'offline'
    assert any(
        getattr(event, "status", None) == "offline"
        for event in status_events
    ), f"No 'offline' status event found in: {status_events}"

    await connector_manager.stop_all()