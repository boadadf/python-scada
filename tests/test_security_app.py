import pytest
from flask import Flask
from openscada_lite.modules.security.model import SecurityModel
from openscada_lite.modules.security.service import SecurityService
from openscada_lite.modules.security.controller import SecurityController

@pytest.fixture
def app(tmp_path):
    # Setup Flask app and SecurityModel with a temp config file
    flask_app = Flask(__name__)
    config_path = tmp_path / "security_config.json"
    config_path.write_text('{"users": [], "groups": []}')
    model = SecurityModel(flask_app)
    service = SecurityService(None, model)
    controller = SecurityController(model, service)
    controller.register_routes(flask_app)
    flask_app.config["TESTING"] = True
    return flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_create_and_get_user(client):
    # Create user
    resp = client.post("/security/users", json={"username": "alice", "password": "secret", "groups": ["admin"]})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["username"] == "alice"

    # Get users
    resp = client.get("/security/users")
    assert resp.status_code == 200
    users = resp.get_json()
    assert any(u["username"] == "alice" for u in users)

def test_create_and_get_group(client):
    # Create group
    resp = client.post("/security/groups", json={"name": "admin", "permissions": ["security_get_users"]})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["name"] == "admin"

    # Get groups
    resp = client.get("/security/groups")
    assert resp.status_code == 200
    groups = resp.get_json()
    assert any(g["name"] == "admin" for g in groups)

def test_update_user_groups(client):
    # Create user
    client.post("/security/users", json={"username": "bob", "password": "pw"})
    # Update groups
    resp = client.put("/security/users/bob/groups", json={"groups": ["admin"]})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["username"] == "bob"
    assert "admin" in data["groups"]

def test_update_group_permissions(client):
    # Create group
    client.post("/security/groups", json={"name": "operator"})
    # Update permissions
    resp = client.put("/security/groups/operator/permissions", json={"permissions": ["security_create_user"]})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "operator"
    assert "security_create_user" in data["permissions"]

def test_get_endpoints(client):
    resp = client.get("/security/endpoints")
    assert resp.status_code == 200
    endpoints = resp.get_json()
    # Should include at least one POST endpoint
    assert any(ep.startswith("security_") for ep in endpoints)

def test_login_success_and_failure(client):
    # Create user
    client.post("/security/users", json={"username": "carol", "password": "pw"})
    # Successful login
    resp = client.post("/security/login", json={"username": "carol", "password": "pw"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["username"] == "carol"

    # Wrong password
    resp = client.post("/security/login", json={"username": "carol", "password": "wrong"})
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["status"] == "error"

    # Unknown user
    resp = client.post("/security/login", json={"username": "nobody", "password": "pw"})
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["status"] == "error"

def test_create_user_missing_fields(client):
    resp = client.post("/security/users", json={"username": "dave"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["status"] == "error"

def test_create_group_missing_name(client):
    resp = client.post("/security/groups", json={"permissions": ["security_get_users"]})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["status"] == "error"

def test_update_user_groups_unknown_user(client):
    resp = client.put("/security/users/ghost/groups", json={"groups": ["admin"]})
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["status"] == "error"

def test_update_group_permissions_unknown_group(client):
    resp = client.put("/security/groups/ghost/permissions", json={"permissions": ["security_get_users"]})
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["status"] == "error"