# -----------------------------------------------------------------------------
# Copyright 2025 Daniel&Hector Fernandez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

# openscada_lite/modules/security/security_service.py
from typing import Optional
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.modules.security.model import SecurityModel
from openscada_lite.common.utils import utils


class SecurityService(BaseService[None, None, None]):
    _instance: Optional["SecurityService"] = None

    def __init__(self, event_bus, model: SecurityModel, controller):
        super().__init__(event_bus, model, controller, None, None, None)
        SecurityService._instance = self
        self.model = model
        self._endpoints = set()  # registered endpoint names

    @classmethod
    def get_instance_or_none(cls) -> Optional["SecurityService"]:
        return cls._instance

    def hash_password(self, password: str) -> str:
        return utils.hash_password(password)

    def authenticate_user(self, username: str, password: str, app_name: Optional[str] = None) -> Optional[str]:
        user = next((u for u in self.model.get_all_users_list() if u["username"] == username), None)
        if not user:
            return None
        if user["password_hash"] != utils.hash_password(password):
            return None
        if app_name and not self.can_login_to(username, app_name):
            return None
        return utils.create_jwt(username, user.get("groups", []))

    def can_login_to(self, username: str, app_name: str) -> bool:
        user = next(
            (u for u in self.model.get_all_users_list() if u["username"] == username),
            None,
        )
        if not user:
            return False
        allowed = user.get("allowed_apps")
        if allowed is None:
            # If not set, allow all apps (or deny, as you prefer)
            return True
        return app_name in allowed

    def is_allowed(self, username: str, endpoint_name: str) -> bool:
        print("Checking if user is allowed:", username, endpoint_name)
        """Check if the given username has permission for the endpoint."""
        user = next(
            (u for u in self.model.get_all_users_list() if u["username"] == username),
            None,
        )
        if not user:
            return False
        for group_name in user.get("groups", []):
            print("Checking permissions for group:", group_name)
            group = next(
                (g for g in self.model.get_all_groups_list() if g["name"] == group_name),
                None,
            )
            print("Permissions for the group:", group.get("permissions", []) )
            if group and endpoint_name in group.get("permissions", []):
                return True
        return False
    
    def should_accept_update(self, tag: None) -> bool:
        return False
