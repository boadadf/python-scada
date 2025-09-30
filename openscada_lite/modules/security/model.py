# openscada_lite/modules/security/model.py
import json
import os
import threading
import copy
from typing import List

from flask import Flask, app

from openscada_lite.common.config.config import Config

class SecurityModel:
    """
    Stores users and groups from a config dict and keeps an in-memory copy.
    """

    def __init__(self, flask_app: Flask = None):
        self._lock = threading.RLock()
        self.file_path = Config.get_instance().get_security_config_path()
        self._load()
        self.endpoints = set()  # registered endpoint names
        self.app = flask_app
        if self.app:
            self._load_endpoints()

    def _load_endpoints(self):
        """Scan Flask app for all registered POST endpoint names."""
        print("[SecurityModel] Scanning Flask app for POST endpoints...")
        with self._lock:
            self.endpoints = set(
                rule.endpoint
                for rule in self.app.url_map.iter_rules()
                if "POST" in rule.methods
            )
            for rule in self.app.url_map.iter_rules():
                if "POST" in rule.methods:
                    print(f"Rule: {rule} endpoint: {rule.endpoint} methods: {rule.methods}")

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path) as f:
                self._data = json.load(f)
        else:
            self._data = {"users": [], "groups": []}
            self._save()

    def _save(self):
        with open(self.file_path, "w") as f:
            json.dump(self._data, f, indent=2)

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

    def get_end_points(self) -> List[str]:
        """
        Returns a list of all unique endpoint names from all groups.
        """
        return sorted(list(self.endpoints))