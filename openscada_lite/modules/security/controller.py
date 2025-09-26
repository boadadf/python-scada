# openscada_lite/modules/security/controller.py
from flask import request
from flask_socketio import emit
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import StatusDTO
from openscada_lite.modules.security.service import SecurityService


class SecurityController(BaseController):
    def validate_request_data(self, data):
        return data

    def register_socketio(self):
        super().register_socketio()

        @self.socketio.on("security_get_users")
        def _get_users():
            users = self.model.get_all_users_list()
            self.socketio.emit("security_users", users)

        @self.socketio.on("security_create_user")
        def _create_user(data):
            self.service.create_user(data["username"], data["password"], data.get("groups", []))
            self.socketio.emit("security_users", self.model.get_all_users_list())

        @self.socketio.on("security_update_user")
        def _update_user(data):
            try:
                self.model.update_user_groups(data["username"], data.get("groups", []))
                self.socketio.emit("security_users", self.model.get_all_users_list())
            except KeyError as e:
                self.socketio.emit("security_ack", StatusDTO(status="error", reason=str(e)).to_dict())

        @self.socketio.on("security_get_groups")
        def _get_groups():
            groups = self.model.get_all_groups_list()
            self.socketio.emit("security_groups", groups)

        @self.socketio.on("security_create_group")
        def _create_group(data):
            self.service.create_group(data["name"], data.get("permissions", []))
            self.socketio.emit("security_groups", self.model.get_all_groups_list())

        @self.socketio.on("security_update_group")
        def _update_group(data):
            try:
                self.model.update_group_permissions(data["name"], data.get("permissions", []))
                self.socketio.emit("security_groups", self.model.get_all_groups_list())
            except KeyError as e:
                self.socketio.emit("security_ack", StatusDTO(status="error", reason=str(e)).to_dict())

        @self.socketio.on("security_get_endpoints")
        def _get_endpoints():
            svc = SecurityService.get_instance_or_none()
            endpoints = svc.get_available_endpoints() if svc else []
            self.socketio.emit("security_endpoints", endpoints)

        @self.socketio.on("security_login")
        def _login(data):
            username = data.get("username")
            password = data.get("password")
            svc = self.service
            if not svc:
                emit("security_login_response", {"status": "error", "reason": "Security not enabled"})
                return

            user = svc.model.get_user(username)
            if not user or svc.hash_password(password) != user["password_hash"]:
                emit("security_login_response", {"status": "error", "reason": "Invalid username or password"})
                return

            # associate sid → username
            sid = request.sid
            self._sid_to_user[sid] = username
            emit("security_login_response", {"status": "ok", "username": username})