import asyncio
import pytest
from fastapi.testclient import TestClient
from openscada_lite.app import app, sio
from unittest.mock import MagicMock
from openscada_lite.web.config_editor.routes import restart_app


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


@pytest.mark.asyncio
async def test_restart_app_docker(monkeypatch):
    # Mock Docker container
    mock_container = MagicMock()
    mock_container.restart = MagicMock()

    # Mock Docker client
    mock_client = MagicMock()
    mock_client.containers.get.return_value = mock_container

    # Patch docker.from_env in the correct namespace
    monkeypatch.setattr(
        "openscada_lite.web.config_editor.routes.docker.from_env",
        lambda: mock_client
    )

    # Patch HOSTNAME
    monkeypatch.setenv("HOSTNAME", "fake_id")

    # Patch asyncio.create_task to schedule the coroutine and store the task
    created_tasks = []

    def create_task_sync(coro):
        task = asyncio.get_event_loop().create_task(coro)
        created_tasks.append(task)
        return task

    monkeypatch.setattr(
        "openscada_lite.web.config_editor.routes.asyncio.create_task",
        create_task_sync
    )

    # Call endpoint
    response = await restart_app()
    # Await all created tasks to ensure background logic runs
    for task in created_tasks:
        await task

    assert response["message"] == "Restarting OpenSCADA-Lite container..."

    # Assert restart happened
    mock_client.containers.get.assert_called_with("fake_id")
    mock_container.restart.assert_called_once()

