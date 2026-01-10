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
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from openscada_lite.common.config.config import Config
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import (
    AnimationUpdateRequestMsg,
    AnimationUpdateMsg,
)
import logging

logger = logging.getLogger(__name__)


class AnimationController(
    BaseController[AnimationUpdateMsg, AnimationUpdateRequestMsg]
):
    def __init__(self, model, socketio, module_name: str, router: APIRouter):
        super().__init__(
            model,
            socketio,
            AnimationUpdateMsg,
            AnimationUpdateRequestMsg,
            module_name,
            router,
        )

        # Load SVG files from config
        self.svg_files = Config.get_instance().get_svg_files()

    def register_local_routes(self, router: APIRouter):
        @router.get("/animation/svgs", tags=[self.base_event], operation_id="getSvgs")
        async def list_svgs():
            logger.debug("Listing SVG files")
            """Return the list of SVG files for the animation module."""
            return JSONResponse(content=self.svg_files)

        @router.get(
            "/animation/svg/{filename:path}",
            tags=[self.base_event],
            operation_id="getSvg",
            response_class=FileResponse,  # Explicitly define response type
            responses={
                200: {
                    "description": "SVG file content",
                    "content": {"text/plain": {}},  # Define plain text response
                },
                404: {
                    "description": "File not found",
                    "content": {"application/json": {}},
                },
            },
        )
        async def svg(filename: str):
            logger.debug(f"Requested SVG file: {filename}")
            svg_dir = (
                Path(__file__).parent.parent.parent.parent.parent / "config" / "svg"
            )
            logger.debug(f"SVG directory: {svg_dir}")
            file = svg_dir / filename
            if file.exists():
                return FileResponse(
                    file, media_type="text/plain"
                )  # Ensure correct media type
            return JSONResponse(content={"error": "File not found"}, status_code=404)

    def validate_request_data(
        self, data: AnimationUpdateRequestMsg
    ) -> AnimationUpdateRequestMsg:
        # You could also return a StatusDTO if invalid
        return data
