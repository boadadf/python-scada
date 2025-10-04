# openscada_lite/modules/security/security_service.py
from typing import Optional, List
from openscada_lite.modules.security.model import SecurityModel
from openscada_lite.modules.security import utils

class SecurityService:
    _instance: Optional["SecurityService"] = None

    def __init__(self, event_bus, model: SecurityModel):
        SecurityService._instance = self
        self.model = model
        self._endpoints = set()  # registered endpoint names

    @classmethod
    def get_instance_or_none(cls) -> Optional["SecurityService"]:
        return cls._instance

    def hash_password(self, password: str) -> str:
        return utils.hash_password(password)

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        user = next((u for u in self.model.get_all_users_list() if u["username"] == username), None)
        if not user:
            return None
        if user["password_hash"] != utils.hash_password(password):
            return None
        return utils.create_jwt(username)

    def is_allowed(self, username: str, endpoint_name: str) -> bool:
        """Check if the given username has permission for the endpoint."""
        user = next((u for u in self.model.get_all_users_list() if u["username"] == username), None)
        if not user:
            return False
        for group_name in user.get("groups", []):
            group = next((g for g in self.model.get_all_groups_list() if g["name"] == group_name), None)
            if group and endpoint_name in group.get("permissions", []):
                return True
        return False
