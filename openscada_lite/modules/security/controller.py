import os
from flask import request, jsonify
from openscada_lite.modules.security.model import SecurityModel
from openscada_lite.common.models.dtos import StatusDTO
from openscada_lite.modules.security.service import SecurityService
from openscada_lite.modules.security import utils
from functools import wraps

class SecurityController:
    """
    REST-style controller for the security module.
    JWT-based authentication. Use register_routes(flask_app) after initialization.
    """

    def __init__(self, model: SecurityModel, service: SecurityService):
        self.model = model
        self.service = service

    # ---------------- JWT Decorator ----------------
    def require_jwt(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            token = auth_header.replace("Bearer ", "")
            username = utils.verify_jwt(token)
            if not username:
                return jsonify(StatusDTO(status="error", reason="Unauthorized").to_dict()), 401
            return func(username=username, *args, **kwargs)
        return wrapper

    # ---------------- Register Routes ----------------
    def register_routes(self, flask_app):

        # ---------------- Endpoints ----------------
        @flask_app.route("/security/endpoints", methods=["GET"])
        def _get_endpoints():
            endpoints = self.model.get_end_points()
            return jsonify(endpoints)

        # ---------------- Login ----------------
        @flask_app.route("/security/login", methods=["POST"])
        def _login():
            data = request.json or {}
            username = data.get("username")
            password = data.get("password")
            app_name = data.get("app") or request.args.get("app")
            if not username or not password or not app_name:
                return jsonify(StatusDTO(status="error", reason="username & password & app required").to_dict()), 400

            # Verify credentials
            token = self.service.authenticate_user(username, password, app_name)
            if not token:
                return jsonify({"error": "Unauthorized"}), 401
            return jsonify({"token": token, "user": username})

        @flask_app.route("/security-editor/api/config", methods=["GET"])
        def get_security_config():
            try:
                config = self.model.get_security_config()
                return jsonify(config)
            except Exception as e:
                return jsonify(StatusDTO(status="error", reason=f"Failed to load: {e}").to_dict()), 500

        # --- Security Editor Config API ---
        @flask_app.route("/security-editor/api/config", methods=["POST"])
        def save_security_config():
            data = request.get_json()
            if not data:
                return jsonify(StatusDTO(status="error", reason="No data provided").to_dict()), 400
            try:
                self.model.save_security_config(data)
            except Exception as e:
                return jsonify(StatusDTO(status="error", reason=f"Failed to save: {e}").to_dict()), 500

            # Notify the system that the config has changed
            # (You can implement this as needed, e.g., reload config, set a flag, etc.)
            if hasattr(self.service, "notify_config_changed"):
                self.service.notify_config_changed()

            return jsonify(StatusDTO(status="ok", reason="Config saved").to_dict())
