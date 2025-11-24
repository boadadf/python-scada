import os
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from fastapi import FastAPI, APIRouter
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport

from openscada_lite.common.models.dtos import (
    DriverConnectCommand,
    DriverConnectStatus,
    RawTagUpdateMsg,
)
from openscada_lite.modules.communication.controller import CommunicationController
from openscada_lite.modules.communication.service import CommunicationService
from openscada_lite.modules.communication.model import CommunicationModel
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.config.config import Config
from openscada_lite.modules.communication.manager.connector_manager import ConnectorManager


# --------------------------
# Fixtures
# --------------------------


@pytest.fixture(autouse=True)
def reset_event_bus(monkeypatch):
    """Reset the EventBus singleton before each test."""
    monkeypatch.setattr(EventBus, "_instance", None)


@pytest.fixture(autouse=True)
def reset_connector_manager(monkeypatch):
    """Reset the ConnectorManager singleton before each test."""
    monkeypatch.setattr(ConnectorManager, "_instance", None)


@pytest.fixture(scope="session", autouse=True)
def set_scada_config_path():
    """Ensure SCADA_CONFIG_PATH points to the test configuration."""
    os.environ["SCADA_CONFIG_PATH"] = "system_config.json"
    print(f"[TEST SETUP] SCADA_CONFIG_PATH set to {os.environ['SCADA_CONFIG_PATH']}")


@pytest.fixture
def dummy_event_bus():
    """Provide a dummy async EventBus for tests."""

    class DummyEventBus:
        def __init__(self):
            self.published = []

        async def publish(self, event_type, data):
            self.published.append((event_type, data))

        def subscribe(self, event_type, handler):
            pass

    return DummyEventBus()


@pytest.fixture
def model():
    return CommunicationModel()


@pytest.fixture
def service(model, dummy_event_bus):
    svc = CommunicationService(dummy_event_bus, model, None)
    return svc, dummy_event_bus, model


@pytest.fixture
def fastapi_app(model):
    """FastAPI app with CommunicationController mounted."""
    app = FastAPI()
    router = APIRouter()
    controller = CommunicationController(model, MagicMock(), "communication", router)
    controller.service = MagicMock()
    app.include_router(controller.router)
    return app, controller


# --------------------------
# Tests: Controller Endpoints
# --------------------------


@pytest.mark.asyncio
async def test_connect_driver_valid_status(fastapi_app):
    app, controller = fastapi_app
    controller.service.handle_controller_message = AsyncMock(return_value=True)

    # Use ASGITransport to wrap the FastAPI app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac: # NOSONAR
        data = DriverConnectCommand(driver_name="WaterTank", status="connect")
        response = await ac.post("/communication_send_driverconnectcommand", json=data.to_dict())

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "reason": "Request accepted."}
    controller.service.handle_controller_message.assert_called_once_with(data)


@pytest.mark.asyncio
async def test_connect_driver_invalid_status(fastapi_app):
    app, controller = fastapi_app
    controller.service.handle_controller_message = AsyncMock(return_value=True)

    # Use ASGITransport to wrap the FastAPI app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac: # NOSONAR
        data = DriverConnectCommand(driver_name="WaterTank", status="bad_status")
        response = await ac.post("/communication_send_driverconnectcommand", json=data.to_dict())

    assert response.status_code == 400
    assert response.json() == {
        "status": "error",
        "reason": "Invalid status. Must be 'connect', 'disconnect', or 'toggle'.",
    }
    controller.service.handle_controller_message.assert_not_called()


@pytest.mark.asyncio
async def test_publish_status_emits(fastapi_app):
    Config.reset_instance()
    Config.get_instance("tests/test_config.json")

    _, controller = fastapi_app

    # Mock socketio.emit as async function
    async_mock = MagicMock()

    async def fake_emit(*args, **kwargs):
        async_mock(*args, **kwargs)

    controller.socketio.emit = fake_emit

    # Create a command message
    cmd = DriverConnectCommand(track_id="1234", driver_name="WaterTank", status="connect")

    # Call publish (synchronous method, no await needed)
    controller.publish(cmd)

    # Wait for the batch worker to process the buffer
    await asyncio.sleep(1.1)  # Slightly longer than the batch interval (1 second)

    # Verify emit was called
    async_mock.assert_called_once()
    args, kwargs = async_mock.call_args

    # Check the event name
    assert args[0] == "communication_driverconnectstatus"

    # Check that the emitted batch contains the expected message
    emitted_batch = args[1]
    assert isinstance(emitted_batch, list), "Expected a batch (list) of messages"
    assert any(
        message["track_id"] == "1234" and message["driver_name"] == "WaterTank"
        for message in emitted_batch
    ), "Expected message not found in emitted batch"

    # Check the room argument
    assert kwargs["room"] == "communication_room"


# --------------------------
# Tests: Service / EventBus
# --------------------------


@pytest.mark.asyncio
async def test_service_publishes_connect_status(service):
    Config.reset_instance()
    Config.get_instance("tests/test_config.json")

    bus = EventBus.get_instance()
    service = CommunicationService(bus, CommunicationModel(), None)

    events = []
    wait_event = asyncio.Event()

    async def handler(evt):
        events.append(evt)
        wait_event.set()

    bus.subscribe(EventType.DRIVER_CONNECT_STATUS, handler)

    await service.async_init()
    await service.handle_controller_message(DriverConnectCommand("WaterTank", "connect"))

    assert any(getattr(e, "driver_name", None) == "WaterTank" for e in events)


@pytest.mark.asyncio
async def test_service_invalid_bus_message_raises(service):
    svc, _, _ = service
    svc.controller = MagicMock()
    with pytest.raises(TypeError):
        await svc.handle_bus_message(
            DriverConnectStatus(track_id="1", driver_name="X", status="connect")
        )


# --------------------------
# Tests: CommunicationModel
# --------------------------


def test_set_and_get_status():
    model = CommunicationModel()
    model.update(DriverConnectStatus("WaterTank", "connect"))
    model.update(DriverConnectStatus("AuxServer", "disconnect"))
    assert {k: v.status for k, v in model.get_all().items()} == {
        "WaterTank": "connect",
        "AuxServer": "disconnect",
    }
    # Ensure model internal dict is not overwritten
    all_status = model.get_all()
    all_status["WaterTank"].status = "disconnect"
    assert model.get_all()["WaterTank"].status == "connect"


def test_driver_initial_status_is_disconnected():
    model = CommunicationModel()
    driver_name = "WaterTank"
    model.update(DriverConnectStatus(driver_name, "disconnect"))
    assert model.get_all()[driver_name].status == "disconnect"


@pytest.mark.asyncio
async def test_driver_publishes_disconnected_status_on_start():
    Config.reset_instance()
    Config.get_instance("tests/test_config.json")
    bus = EventBus.get_instance()
    service = CommunicationService(bus, CommunicationModel(), None)
    manager = service.connection_manager

    events = []
    wait_event = asyncio.Event()

    async def handler(evt):
        events.append(evt)
        wait_event.set()

    bus.subscribe(EventType.DRIVER_CONNECT_STATUS, handler)

    await manager.start_all()
    await asyncio.wait_for(wait_event.wait(), timeout=2.0)
    assert any(getattr(e, "status", None) == "offline" for e in events)
    await manager.stop_all()


@pytest.mark.asyncio
async def test_emit_communication_status(monkeypatch):
    class DummyConfig:
        def get_datapoint_types_for_driver(self, driver_name, types):
            if driver_name == "TestDriver":
                return {"TANK": {"default": 0.0}, "PUMP": {"default": "CLOSED"}}
            return {}

        def get_drivers(self):
            return []

        def get_types(self):
            return {}

    monkeypatch.setattr(
        "openscada_lite.common.config.config.Config.get_instance", lambda: DummyConfig()
    )

    bus = EventBus.get_instance()
    published = []

    async def fake_publish(self, event_type, data):
        published.append((event_type, data))

    monkeypatch.setattr(EventBus, "publish", fake_publish)

    service = CommunicationService(bus, CommunicationModel(), None)
    manager = service.connection_manager
    manager.driver_status["TestDriver"] = "online"

    status = DriverConnectStatus(driver_name="TestDriver", status="offline")
    await manager.emit_communication_status(status)

    raw_updates = [d for e, d in published if e == EventType.RAW_TAG_UPDATE]
    assert len(raw_updates) == 2
    for msg in raw_updates:
        assert isinstance(msg, RawTagUpdateMsg)
        assert msg.quality == "unknown"
        assert msg.datapoint_identifier in ["TestDriver@TANK", "TestDriver@PUMP"]
        if msg.datapoint_identifier.endswith("TANK"):
            assert msg.value == 0.0
        elif msg.datapoint_identifier.endswith("PUMP"):
            assert msg.value == "CLOSED"
