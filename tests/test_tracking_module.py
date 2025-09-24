import asyncio
from datetime import datetime
import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock

from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.tracking.utils import safe_serialize
from openscada_lite.common.config.config import Config
from openscada_lite.modules.tracking.model import TrackingModel
from openscada_lite.modules.tracking.controller import TrackingController
from openscada_lite.modules.tracking.service import TrackingService
from openscada_lite.common.models.dtos import DataFlowEventMsg, DataFlowStatus
from openscada_lite.common.bus.event_types import EventType

@pytest.fixture
def sample_event():
    return DataFlowEventMsg(
        track_id="abc123",
        event_type="TestEvent",
        source="UnitTest",
        status=DataFlowStatus.SUCCESS,
        timestamp=datetime.fromisoformat("2025-09-24T12:00:00"),
        payload={"foo": "bar"}
    )

@pytest.fixture
def model():
    return TrackingModel()

@pytest.fixture
def controller(model):
    socketio = MagicMock()
    return TrackingController(model, socketio)

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
    config = Config.get_instance("tests/test_config.json")
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
async def test_service_file_mode_reads_new_events(tmp_path, model, controller, sample_event):
    file_path = tmp_path / "flow_events.log"

    # Configure tracking to use file mode
    config = Config.get_instance("tests/test_config.json")
    config.get_module_config("tracking")["mode"] = "file"
    config.get_module_config("tracking")["file_path"] = str(file_path)

    service = TrackingService(EventBus.get_instance(), model, controller)
    #Ensure the file exists
    open(file_path, "a").close()
    # Start tailing in the background (do NOT read old lines)
    task = asyncio.create_task(service.tail_file(str(file_path), from_start=False))
    await asyncio.sleep(0.5)  # ensure f.seek(END) has run
    with open(file_path, "a") as f:
        f.write(json.dumps(sample_event.get_track_payload(), default=safe_serialize) + "\n")
        f.flush()
    await asyncio.sleep(1)  # allow processing
    
    # Check that the event was loaded into the model
    events = list(model.get_all().values())
    assert any(e.track_id == sample_event.track_id for e in events)
    
    # Cleanup
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    if os.path.exists(file_path):
        os.remove(file_path)

def test_controller_publish_live_feed(model):
    socketio = MagicMock()
    controller = TrackingController(model, socketio)
    event = DataFlowEventMsg(
        track_id="abc123",
        event_type="TestEvent",
        source="UnitTest",
        status=DataFlowStatus.SUCCESS,
        timestamp="2025-09-24T12:00:00",
        payload={"foo": "bar"}
    )
    controller.publish(event)
    socketio.emit.assert_called_once()
    args, kwargs = socketio.emit.call_args
    assert args[0] == "tracking_datafloweventmsg"
    assert args[1]["track_id"] == "abc123"

def test_model_add_and_get_events(model: TrackingModel, sample_event):
    model.update(sample_event)
    events = list(model.get_all().values())
    assert len(events) == 1
    assert events[0] == sample_event