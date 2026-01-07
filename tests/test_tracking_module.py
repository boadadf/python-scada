import asyncio
from datetime import datetime
import pytest
from unittest.mock import MagicMock
from fastapi import APIRouter

from openscada_lite.common.config.config import Config
from openscada_lite.modules.tracking.model import TrackingModel
from openscada_lite.modules.tracking.controller import TrackingController
from openscada_lite.modules.tracking.service import TrackingService
from openscada_lite.common.models.dtos import DataFlowEventMsg, DataFlowStatus


@pytest.fixture
def sample_event():
    return DataFlowEventMsg(
        track_id="abc123",
        event_type="TestEvent",
        source="UnitTest",
        status=DataFlowStatus.SUCCESS,
        timestamp=datetime.fromisoformat("2025-09-24T12:00:00"),
        payload={"foo": "bar"},
    )


@pytest.fixture
def model():
    return TrackingModel()


@pytest.fixture
def controller(model):
    socketio = MagicMock()
    module_name = "tracking"
    router = APIRouter()

    # Create the TrackingController instance
    return TrackingController(model, socketio, module_name, router)


@pytest.mark.asyncio
async def test_service_bus_mode_adds_event(model, controller, sample_event):
    # Mock event bus
    class DummyBus:
        def __init__(self):
            self.subscribed = {}

        def subscribe(self, event_type, callback):
            self.subscribed[event_type] = callback

        def publish(self, event_type, event):
            if event_type in self.subscribed:
                asyncio.create_task(self.subscribed[event_type](event))

    event_bus = DummyBus()
    config = Config.get_instance("tests/config/test_config.json")
    config.get_module_config("tracking")["mode"] = "bus"
    service = TrackingService(event_bus, model, controller)
    # Simulate event bus publishing
    await service.handle_bus_message(sample_event)
    events = list(model.get_all().values())
    stored = events[0]
    assert stored.track_id == sample_event.track_id
    assert stored.event_type == sample_event.event_type
    assert stored.source == sample_event.source
    assert stored.status == sample_event.status
    assert stored.timestamp == sample_event.timestamp
    assert stored.payload == sample_event.payload


@pytest.mark.asyncio
async def test_controller_publish_live_feed(model):
    socketio = MagicMock()
    module_name = "tracking"
    router = APIRouter()

    # Create the TrackingController instance with the required parameters
    controller = TrackingController(model, socketio, module_name, router)

    # Create a sample event
    event = DataFlowEventMsg(
        track_id="abc123",
        event_type="TestEvent",
        source="UnitTest",
        status=DataFlowStatus.SUCCESS,
        timestamp="2025-09-24T12:00:00",
        payload={"foo": "bar"},
    )

    # Publish the event
    controller.publish(event)

    # Wait for the batch worker to process the buffer
    await asyncio.sleep(1.1)  # Slightly longer than the batch interval (1 second)

    # Assert that the event was emitted via Socket.IO
    socketio.emit.assert_called_once()
    args, kwargs = socketio.emit.call_args
    assert args[0] == "tracking_datafloweventmsg"
    assert any(
        emitted_event["track_id"] == "abc123"
        and emitted_event["event_type"] == "TestEvent"
        for emitted_event in args[1]
    )


def test_model_add_and_get_events(model: TrackingModel, sample_event):
    model.update(sample_event)
    events = list(model.get_all().values())
    assert len(events) == 1
    assert events[0] == sample_event
