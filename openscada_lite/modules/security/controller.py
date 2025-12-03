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
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from openscada_lite.common.tracking.decorators import publish_route_async
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.modules.security.model import SecurityModel
from openscada_lite.common.models.dtos import StatusDTO
from openscada_lite.common.utils import SecurityUtils
from openscada_lite.common.utils.ResponseUtils import make_response
import logging

logger = logging.getLogger(__name__)


class SecurityController(
    BaseController[None, None],
):

    def __init__(self, model: SecurityModel, socketio, module_name: str, router: APIRouter):
        super().__init__(model, socketio, None, None, module_name, router)
        self.model = model

    # ---------------- JWT Dependency ----------------
    async def require_jwt(self, request: Request) -> str:
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "")
        username = SecurityUtils.verify_jwt(token)
        if not username:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return username

    # ---------------- Register Routes ----------------
    def register_local_routes(self, router: APIRouter):
        logger.debug("[SECURITY] Loading security routes")
        self.model.load_endpoints(router)

        # GET all registered endpoints
        @router.get("/security/endpoints")
        async def get_endpoints():
            endpoints = self.model.get_end_points()
            return JSONResponse(content=endpoints)

        logger.debug("[SECURITY] Registered endpoints route loaded")

        # POST login
        @router.post("/security/login")
        @publish_route_async(DataFlowStatus.USER_ACTION, source="SecurityController")
        async def login(data: dict, app: str = None):
            logger.debug("[SECURITY] Login request received")
            username = data.get("username")
            password = data.get("password")
            app_name = app if app is not None else data.get("app")
            logger.debug(f"[SECURITY] Login attempt for user: {username}, app: {app_name}")
            if not username or not password or not app_name:
                logger.warning("[SECURITY] Missing username, password, or app")
                return make_response(
                    status="error",
                    reason="username & password & app required",
                    status_code=400,
                    user=username,
                    endpoint="login",
                )

            token = self.service.authenticate_user(username, password, app_name)
            if not token:
                logger.warning("[SECURITY] Authentication failed")
                return make_response(
                    status="error",
                    reason="Unauthorized",
                    status_code=401,
                    user=username,
                    endpoint="login",
                )

            logger.info(f"[SECURITY] User authenticated: {username}")
            return make_response(
                status="ok",
                reason="Login successful",
                status_code=200,
                data={"token": token},  # keep token here
                user=username,
                endpoint="login",
            )

        # GET security config
        @router.get("/security-editor/api/config")
        async def get_security_config():
            try:
                config = self.model.get_security_config()
                return JSONResponse(content=config)
            except Exception as e:
                return JSONResponse(
                    content=StatusDTO(status="error", reason=f"Failed to load: {e}").to_dict(),
                    status_code=500,
                )

        # POST security config
        @router.post("/security-editor/api/config")
        async def save_security_config(data: dict):
            if not data:
                return JSONResponse(
                    content=StatusDTO(status="error", reason="No data provided").to_dict(),
                    status_code=400,
                )
            try:
                self.model.save_security_config(data)
            except Exception as e:
                return JSONResponse(
                    content=StatusDTO(status="error", reason=f"Failed to save: {e}").to_dict(),
                    status_code=500,
                )
            # Notify service if applicable
            if hasattr(self.service, "notify_config_changed"):
                self.service.notify_config_changed()
            return JSONResponse(content=StatusDTO(status="ok", reason="Config saved").to_dict())

    def validate_request_data(self, data: dict, required_fields: list) -> bool:
        return False
