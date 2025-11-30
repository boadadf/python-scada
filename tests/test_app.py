import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from openscada_lite.app import app, sio


@pytest.fixture
def test_client():
    """Fixture to create a FastAPI test client."""
    return TestClient(app)


def test_fastapi_initialization(test_client):
    """Test that the FastAPI app initializes correctly."""
    response = test_client.get("/docs")  # Check if the OpenAPI docs are available
    assert response.status_code == 200
    assert "OpenSCADA-Lite" in response.text


def test_socketio_initialization():
    """Test that the Socket.IO server is initialized correctly."""
    assert sio.async_mode == "asgi"
    # Check if the configuration matches the expected values
    assert sio.eio.ping_interval == 25
    assert sio.eio.ping_timeout == 120
