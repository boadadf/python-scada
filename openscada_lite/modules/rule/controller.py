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

# communications_controller.py
from fastapi import APIRouter
from openscada_lite.modules.base.base_controller import BaseController


class RuleController(BaseController[None, None]):
    def __init__(self, model, socketio, module_name: str, router: APIRouter):
        super().__init__(
            model, socketio, None, None, module_name, router
        )

    def validate_request_data(self, data):
        # No validation needed (no U type)
        return data
