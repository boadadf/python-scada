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

    def get_all_users_list(self) -> List[dict]:
        with self._lock:
            return copy.deepcopy(self._data["users"])

    def get_end_points(self) -> List[str]:
        """
        Returns a list of all unique endpoint names from all groups.
        """
        return sorted(list(self.endpoints))
    
    def get_security_config(self) -> dict:
        with self._lock:
            return copy.deepcopy(self._data)    
        
    def save_security_config(self, config: dict):
        with self._lock:
            self._data = copy.deepcopy(config)
            self._save()