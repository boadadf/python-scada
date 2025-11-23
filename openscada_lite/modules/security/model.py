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

# openscada_lite/modules/security/model.py
import json
import os
import copy
import threading
from typing import List

from fastapi import APIRouter
from openscada_lite.modules.base.base_model import BaseModel
from openscada_lite.common.config.config import Config


class SecurityModel(BaseModel[None]):

    def __init__(self):
        super().__init__()
        self._lock = threading.RLock()  # Initialize _lock first
        self.file_path = Config.get_instance().get_security_config_path()
        self.endpoints = set()  # registered endpoint names
        self._load()

    def load_endpoints(self, router: APIRouter):
        """Scan FastAPI app for all registered POST endpoint names."""
        with self._lock:
            self.endpoints = set(
                route.name for route in router.routes if "POST" in getattr(route, "methods", [])
            )

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path) as f:
                self._data = json.load(f)
        else:
            self._data = {"users": [], "groups": []}
            self._save()

    def _save(self):
        with self._lock:
            with open(self.file_path, "w") as f:
                json.dump(self._data, f, indent=2)

    def get_all_users_list(self) -> List[dict]:
        with self._lock:
            return copy.deepcopy(self._data["users"])

    def get_end_points(self) -> List[str]:
        return sorted(list(self.endpoints))

    def get_security_config(self) -> dict:
        with self._lock:
            return copy.deepcopy(self._data)

    def save_security_config(self, config: dict):
        with self._lock:
            self._data = copy.deepcopy(config)
            self._save()
