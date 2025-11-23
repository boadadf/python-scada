import pytest
import json
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from openscada_lite.modules.security.model import SecurityModel
from openscada_lite.modules.security.service import SecurityService
from openscada_lite.modules.security.controller import SecurityController


@pytest.fixture
def app(tmp_path):
    """Create a FastAPI app with SecurityController mounted."""
    # Create a FastAPI app
    app = FastAPI()

    # Create a temporary security configuration file
    config_path = tmp_path / "security_config.json"
    config_path.write_text(json.dumps({"users": [], "groups": []}))

    # Initialize the SecurityModel
    model = SecurityModel()

    # Create an APIRouter
    router = APIRouter()

    # Initialize the SecurityController
    socketio = MagicMock()
    controller = SecurityController(model, socketio, "security", router)

    # Create the SecurityService
    event_bus = MagicMock()
    service = SecurityService(event_bus, model, controller)

    # Include the router in the FastAPI app
    app.include_router(router)

    # Return the FastAPI app, model, controller, and service for testing
    return app, model, controller, service


@pytest.fixture
def client(app):
    app, _, _, _ = app
    return TestClient(app)


def test_full_config_roundtrip(client):
    # Prepare full config JSON
    config = {
        "groups": [
            {
                "name": "all_group",
                "permissions": [
                    "alarm_send_ackalarmmsg",
                    "command_send_sendcommandmsg",
                    "communication_send_driverconnectcommand",
                    "config_bp.reload_modules",
                    "config_bp.save_config",
                    "datapoint_send_rawtagupdatemsg",
                    "security_bp.reload_security",
                    "security_bp.save_config",
                    "animation_send_animationupdaterequestmsg",
                ],
            }
        ],
        "users": [
            {
                "allowed_apps": ["security_editor", "config_editor", "scada"],
                "groups": ["all_group"],
                "password_hash": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",  # hash for 'admin'
                "username": "admin",
            }
        ],
    }

    # Save config
    resp = client.post("/security-editor/api/config", json=config)
    assert resp.status_code == 200

    # Load config
    resp = client.get("/security-editor/api/config")
    assert resp.status_code == 200
    loaded = resp.json()
    assert loaded == config

    # Check users/groups structure
    assert "users" in loaded and "groups" in loaded
    assert loaded["users"][0]["username"] == "admin"
    assert loaded["groups"][0]["name"] == "all_group"


def test_login_admin(client):
    # Prepare config with admin user (password: 'admin')
    config = {
        "groups": [{"name": "test_group", "permissions": ["security_editor_access"]}],
        "users": [
            {
                "allowed_apps": ["security_editor"],
                "groups": ["test_group"],
                "password_hash": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",  # hash for 'admin'
                "username": "admin",
            }
        ],
    }
    client.post("/security-editor/api/config", json=config)

    # Try login with admin/admin
    resp = client.post(
        "/security/login",
        json={"username": "admin", "password": "admin", "app": "security_editor"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"] == "admin"


def test_invalid_login(client):
    # Prepare config with admin user
    config = {
        "groups": [{"name": "test_group", "permissions": []}],
        "users": [
            {
                "allowed_apps": ["security_editor"],
                "groups": ["test_group"],
                "password_hash": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",
                "username": "admin",
            }
        ],
    }
    client.post("/security-editor/api/config", json=config)

    # Wrong password
    resp = client.post(
        "/security/login",
        json={"username": "admin", "password": "wrong", "app": "security_editor"},
    )
    assert resp.status_code == 401

    # Unknown user
    resp = client.post(
        "/security/login",
        json={"username": "ghost", "password": "admin", "app": "security_editor"},
    )
    assert resp.status_code == 401


def test_missing_fields(client):
    # POST config missing users/groups
    resp = client.post("/security-editor/api/config", json={})
    assert resp.status_code == 400 or resp.status_code == 422


def test_permissions_structure(client):
    # Save config with multiple groups/permissions
    config = {
        "groups": [
            {"name": "g1", "permissions": ["p1", "p2"]},
            {"name": "g2", "permissions": ["p3"]},
        ],
        "users": [
            {
                "username": "u1",
                "groups": ["g1"],
                "allowed_apps": [],
                "password_hash": "",
            },
            {
                "username": "u2",
                "groups": ["g2"],
                "allowed_apps": [],
                "password_hash": "",
            },
        ],
    }
    resp = client.post("/security-editor/api/config", json=config)
    assert resp.status_code == 200
    resp = client.get("/security-editor/api/config")
    assert resp.status_code == 200
    loaded = resp.json()
    assert len(loaded["groups"]) == 2
    assert len(loaded["users"]) == 2
    assert loaded["groups"][0]["permissions"] == ["p1", "p2"]
    assert loaded["groups"][1]["permissions"] == ["p3"]
