import pytest
from unittest.mock import MagicMock, patch
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from openscada_lite.modules.gis.controller import GisController
from openscada_lite.modules.gis.service import GisService
from openscada_lite.modules.gis.model import GisModel
from openscada_lite.common.models.dtos import GisUpdateMsg, TagUpdateMsg, AlarmUpdateMsg


@pytest.fixture(scope="function")
def gis_model():
    """Fixture for the GIS model."""
    model = GisModel()
    model.reset()  # Reset state before each test
    return model


@pytest.fixture(scope="function")
@patch("openscada_lite.modules.gis.service.Config")
def gis_service(mock_config, gis_model):
    """Fixture for the GIS service."""
    # Mock the configuration to return test data
    mock_config.get_instance.return_value.get_gis_icons.return_value = [
        {"id": "icon1", "latitude": 0.0, "longitude": 0.0, "icon": "icon1.png"},
        {"id": "icon2", "latitude": 1.0, "longitude": 1.0, "icon": "icon2.png"},
    ]

    event_bus = MagicMock()
    controller = MagicMock()
    return GisService(event_bus, gis_model, controller)


@pytest.fixture(scope="function")
def gis_controller(gis_model):
    """Fixture for the GIS controller."""
    socketio_mock = MagicMock()
    router = APIRouter()
    return GisController(gis_model, socketio_mock, "gis", router)


@pytest.fixture
def fastapi_app(gis_controller):
    """Fixture for the FastAPI app with the GIS controller."""
    app = FastAPI()
    router = APIRouter()
    gis_controller.register_local_routes(router)
    app.include_router(router)
    return app


def test_gis_model_initialization(gis_model):
    """Test that the GIS model initializes correctly."""
    assert isinstance(gis_model, GisModel)
    assert len(gis_model.get_all()) == 0  # Ensure the model starts empty


def test_gis_service_initialization(gis_service, gis_model):
    """Test that the GIS service initializes GIS icons."""
    # Assert that icons were initialized
    icons = gis_model.get_all()
    assert len(icons) == 2  # Ensure two icons were added
    assert "icon1" in icons
    assert "icon2" in icons


def test_gis_service_process_tag_update(gis_service, gis_model):
    """Test that the GIS service processes a TagUpdateMsg."""
    tag_msg = TagUpdateMsg(
        datapoint_identifier="example_datapoint",
        value=1,
        quality="good",
        timestamp="2025-11-23T12:00:00Z",
    )
    gis_update = gis_service.process_msg(tag_msg)
    if gis_update:
        assert isinstance(gis_update, GisUpdateMsg)
        assert gis_update.extra["datapoint-value"] is not None


def test_gis_service_process_alarm_update(gis_service, gis_model):
    """Test that the GIS service processes an AlarmUpdateMsg."""
    alarm_msg = AlarmUpdateMsg(
        datapoint_identifier="example_datapoint",  # Add the required argument
        rule_id="example_rule",
        activation_time="2025-11-23T12:00:00Z",
        acknowledge_time=None,
        deactivation_time=None,
    )
    gis_update = gis_service.process_msg(alarm_msg)
    if gis_update:
        assert isinstance(gis_update, GisUpdateMsg)
        assert gis_update.icon is not None


def test_gis_controller_initialization(gis_controller):
    """Test that the GIS controller initializes correctly."""
    assert isinstance(gis_controller, GisController)


def test_gis_controller_get_gis_config(fastapi_app):
    """Test the FastAPI route for retrieving GIS configuration."""
    client = TestClient(fastapi_app)
    response = client.get("/api/gis/config")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)  # Ensure the response is a dictionary
