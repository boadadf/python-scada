import os
import pytest
from fastapi.testclient import TestClient
from openscada_lite.app import app, main, sio


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


@patch("os.environ", {})
@patch("uvicorn.run")
def test_main_without_scada_config_path(mock_uvicorn_run):
    """Test the main() function when SCADA_CONFIG_PATH is not set."""
    with patch("sys.argv", ["app.py"]):
        main()

    # Normalize the expected and actual paths
    expected_path = os.path.normpath(
        os.path.dirname(os.path.dirname(__file__)) + "/config/system_config.json"
    )
    actual_path = os.path.normpath(os.environ["SCADA_CONFIG_PATH"])
    assert actual_path == expected_path

    # Verify that uvicorn.run is called with the correct arguments
    mock_uvicorn_run.assert_called_once_with(
        "openscada_lite.app:asgi_app",
        host="0.0.0.0",
        port=5443,
        reload=True,
        ws_max_size=16 * 1024 * 1024,
    )
