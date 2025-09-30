# openscada_lite/modules/security/controller.py
import typing as t
from flask import request, jsonify
from openscada_lite.common.models.dtos import StatusDTO
from openscada_lite.modules.security.service import SecurityService
from openscada_lite.modules.security.model import SecurityModel

class SecurityController:
    """
    REST-style controller for the security module.
    Use register_routes(flask_app) after initialization to expose endpoints.
    """

    def __init__(self, model: SecurityModel, service: SecurityService):
        self.model = model
        self.service = service

    def register_routes(self, flask_app):
        """
        Register HTTP endpoints on the provided Flask app.
        We use add_url_rule with explicit endpoint names to avoid collisions.
        """

        # ---------------- Users ----------------
        def _get_users():
            users = self.model.get_all_users_list()
            return jsonify(users)
        flask_app.add_url_rule(
            "/security/users", endpoint="security_get_users", view_func=_get_users, methods=["GET"]
        )

        def _create_user():
            data = request.get_json() or {}
            username = data.get("username")
            password = data.get("password")
            groups = data.get("groups", [])
            if not username or not password:
                return jsonify(StatusDTO(status="error", reason="username & password required").to_dict()), 400
            if self.service:
                user = self.service.create_user(username, password, groups)
            else:
                # If no service, write directly via model (store password hash)
                from hashlib import sha256
                password_hash = sha256(password.encode()).hexdigest()
                self.model.add_user({"username": username, "password_hash": password_hash, "groups": groups})
                user = self.model.get_all_users_list()[-1] if self.model.get_all_users_list() else {}
            return jsonify({"status": "ok", "username": username})
        flask_app.add_url_rule(
            "/security/users", endpoint="security_create_user", view_func=_create_user, methods=["POST"]
        )

        def _update_user_groups(username):
            data = request.get_json() or {}
            groups = data.get("groups", [])
            try:
                self.model.update_user_groups(username, groups)
                return jsonify({"status": "ok", "username": username, "groups": groups})
            except KeyError as e:
                return jsonify(StatusDTO(status="error", reason=str(e)).to_dict()), 404
        flask_app.add_url_rule(
            "/security/users/<username>/groups",
            endpoint="security_update_user_groups",
            view_func=_update_user_groups,
            methods=["PUT"]
        )

        # ---------------- Groups ----------------
        def _get_groups():
            groups = self.model.get_all_groups_list()
            return jsonify(groups)
        flask_app.add_url_rule(
            "/security/groups", endpoint="security_get_groups", view_func=_get_groups, methods=["GET"]
        )

        def _create_group():
            data = request.get_json() or {}
            name = data.get("name")
            permissions = data.get("permissions", [])
            if not name:
                return jsonify(StatusDTO(status="error", reason="name required").to_dict()), 400
            if self.service:
                self.service.create_group(name, permissions)
            else:
                self.model.add_group({"name": name, "permissions": permissions})
            return jsonify({"status": "ok", "name": name})
        flask_app.add_url_rule(
            "/security/groups", endpoint="security_create_group", view_func=_create_group, methods=["POST"]
        )

        def _update_group_permissions(group_name):
            data = request.get_json() or {}
            permissions = data.get("permissions", [])
            try:
                self.model.update_group_permissions(group_name, permissions)
                return jsonify({"status": "ok", "name": group_name, "permissions": permissions})
            except KeyError as e:
                return jsonify(StatusDTO(status="error", reason=str(e)).to_dict()), 404
        flask_app.add_url_rule(
            "/security/groups/<group_name>/permissions",
            endpoint="security_update_group_permissions",
            view_func=_update_group_permissions,
            methods=["PUT"]
        )

        # ---------------- Endpoints (available send_* endpoints) ----------------
        def _get_endpoints():            
            endpoints = self.model.get_end_points()
            return jsonify(endpoints)
        flask_app.add_url_rule(
            "/security/endpoints", endpoint="security_get_endpoints", view_func=_get_endpoints, methods=["GET"]
        )

        # ---------------- Login ----------------
        def _login():
            data = request.get_json() or {}
            username = data.get("username")
            password = data.get("password")
            if not username or not password:
                return jsonify(StatusDTO(status="error", reason="username & password required").to_dict()), 400

            svc = self.service or SecurityService.get_instance_or_none()
            # If a service exists, use it (so hashing is consistent). Otherwise use model data & sha256.
            if svc:
                user = next((u for u in svc.model.get_all_users_list() if u["username"] == username), None)
                if not user:
                    return jsonify(StatusDTO(status="error", reason="unknown user").to_dict()), 404
                # compare hashes
                if svc.hash_password(password) != user.get("password_hash"):
                    return jsonify(StatusDTO(status="error", reason="invalid credentials").to_dict()), 401
            else:
                # fallback read from model directly
                user = next((u for u in self.model.get_all_users_list() if u["username"] == username), None)
                if not user:
                    return jsonify(StatusDTO(status="error", reason="unknown user").to_dict()), 404
                import hashlib
                if hashlib.sha256(password.encode()).hexdigest() != user.get("password_hash"):
                    return jsonify(StatusDTO(status="error", reason="invalid credentials").to_dict()), 401

            # success: frontend is expected to store username locally and send X-User later
            return jsonify({"status": "ok", "username": username})
        flask_app.add_url_rule("/security/login", endpoint="security_login", view_func=_login, methods=["POST"])
