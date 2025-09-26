# openscada_lite/modules/security/model.py
import json
import os
import threading
import copy
from typing import List

class SecurityModel:
    """
    Stores users and groups in a JSON file and keeps an in-memory copy.
    """

    def __init__(self, file_path: str = "security.json"):
        self.file_path = file_path
        self._lock = threading.RLock()
        self._data = {"users": [], "groups": []}
        self._load()

    # ---------------- Persistence ----------------
    def _load(self) -> None:
        with self._lock:
            if not os.path.exists(self.file_path):
                self._save()
                return
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                self._data.setdefault("users", [])
                self._data.setdefault("groups", [])
            except Exception:
                self._data = {"users": [], "groups": []}

    def _save(self) -> None:
        with self._lock:
            tmp_path = f"{self.file_path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.file_path)

    # ---------------- Users API ----------------
    def get_all_users_list(self) -> List[dict]:
        with self._lock:
            return copy.deepcopy(self._data["users"])

    def add_user(self, user: dict) -> None:
        if "username" not in user:
            raise ValueError("User must have a username")
        with self._lock:
            for i, u in enumerate(self._data["users"]):
                if u["username"] == user["username"]:
                    self._data["users"][i] = copy.deepcopy(user)
                    self._save()
                    return
            self._data["users"].append(copy.deepcopy(user))
            self._save()

    def update_user_groups(self, username: str, groups: List[str]) -> None:
        with self._lock:
            for u in self._data["users"]:
                if u["username"] == username:
                    u["groups"] = groups[:]
                    self._save()
                    return
            raise KeyError(f"Unknown user: {username}")

    # ---------------- Groups API ----------------
    def get_all_groups_list(self) -> List[dict]:
        with self._lock:
            return copy.deepcopy(self._data["groups"])

    def add_group(self, group: dict) -> None:
        if "name" not in group:
            raise ValueError("Group must have a name")
        with self._lock:
            for i, g in enumerate(self._data["groups"]):
                if g["name"] == group["name"]:
                    self._data["groups"][i] = copy.deepcopy(group)
                    self._save()
                    return
            self._data["groups"].append(copy.deepcopy(group))
            self._save()

    def update_group_permissions(self, name: str, permissions: List[str]) -> None:
        with self._lock:
            for g in self._data["groups"]:
                if g["name"] == name:
                    g["permissions"] = permissions[:]
                    self._save()
                    return
            raise KeyError(f"Unknown group: {name}")
