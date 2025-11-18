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
from openscada_lite.common.config.config import Config
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import (
    AnimationUpdateRequestMsg,
    AnimationUpdateMsg,
)

class AnimationController(
    BaseController[AnimationUpdateMsg, AnimationUpdateRequestMsg]
):
    def __init__(self, model, socketio, base_event="animation"):
        super().__init__(
            model,
            socketio,
            AnimationUpdateMsg,
            AnimationUpdateRequestMsg,
            base_event=base_event,
        )

        # Load SVG files from config
        self.svg_files = Config.get_instance().get_svg_files()

        # Create FastAPI router for HTTP endpoints
        self.router = APIRouter(prefix="/api/animation", tags=["Animation"])
        self.register_routes(self.router)

    def register_routes(self, router: APIRouter):
        @router.get("/svgs")
        async def list_svgs():
            """Return the list of SVG files for the animation module."""
            return JSONResponse(content=self.svg_files)

    def validate_request_data(
        self, data: AnimationUpdateRequestMsg
    ) -> AnimationUpdateRequestMsg:
        # You could also return a StatusDTO if invalid
        return data
    