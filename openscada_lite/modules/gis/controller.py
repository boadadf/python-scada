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
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import GisUpdateMsg
from openscada_lite.common.config.config import Config


class GisController(BaseController[GisUpdateMsg, None]):
    """
    FastAPI-compatible controller for GIS module.
    Handles Socket.IO events via BaseController and HTTP endpoints via APIRouter.
    """

    def __init__(self, model, socketio, module_name:str, router: APIRouter):
        super().__init__(
            model,
            socketio,
            GisUpdateMsg,
            None,
            module_name,
            router
        )
            
    # FastAPI route registration
    def register_local_routes(self, router: APIRouter):
        @router.get("/api/gis/config")
        async def get_gis_config():
            """Expose the GIS configuration from system_config.json."""
            config = Config.get_instance().get_module_config("gis")
            print(f"[GIS] Returning GIS config: {config}")
            return JSONResponse(content=config)

    # Required abstract method from BaseController
    def validate_request_data(self, data):
        return data