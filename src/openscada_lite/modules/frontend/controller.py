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
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.config.config import Config


class FrontendController(BaseController):
    def __init__(self, model, socketio, module_name: str, router: APIRouter):
        super().__init__(model, socketio, None, None, module_name, router)
        self.tabs = Config.get_instance().get_module_config("frontend").get("tabs", [])

    def validate_request_data(self, data):
        return data

    def register_local_routes(self, router: APIRouter):
        @router.get("/frontend/tabs", tags=[self.base_event], operation_id="getTabs")
        async def get_tabs():
            return JSONResponse(content=self.tabs)

        @router.get("/frontend/ping", tags=[self.base_event], operation_id="ping")
        async def ping():
            return {
                "status": "ok",
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            }
