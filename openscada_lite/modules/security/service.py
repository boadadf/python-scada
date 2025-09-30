# openscada_lite/modules/security/security_service.py
import hashlib
from typing import Optional, List
from openscada_lite.modules.security.model import SecurityModel

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
        return hashlib.sha256(password.encode()).hexdigest()

    # ---------------- Users ----------------
    def create_user(self, username: str, password: str, groups: Optional[List[str]] = None):
        user = {
            "username": username,
            "password_hash": self.hash_password(password),
            "groups": groups or []
        }
        self.model.add_user(user)
        return user

    # ---------------- Groups ----------------
    def create_group(self, name: str, permissions: Optional[List[str]] = None):
        group = {
            "name": name,
            "permissions": permissions or []
        }
        self.model.add_group(group)
        return group

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
