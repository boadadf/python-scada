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
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from openscada_lite.modules.security.model import SecurityModel
from openscada_lite.modules.security.service import SecurityService
from openscada_lite.common.models.dtos import StatusDTO
from openscada_lite.modules.security import utils


class SecurityController:
    """
    FastAPI-compatible controller for the Security module.
    JWT-based authentication. Use register_routes(app) after initialization.
    """

    def __init__(self, model: SecurityModel, service: SecurityService):
        self.model = model
        self.service = service
        self.router = APIRouter(prefix="/security", tags=["Security"])

        # Register all endpoints
        self._register_routes()

    # ---------------- JWT Dependency ----------------
    async def require_jwt(self, request: Request) -> str:
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "")
        username = utils.verify_jwt(token)
        if not username:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return username

    # ---------------- Register Routes ----------------
    def _register_routes(self):
        # GET all registered endpoints
        @self.router.get("/endpoints")
        async def get_endpoints():
            endpoints = self.model.get_end_points()
            return JSONResponse(content=endpoints)

        # POST login
        @self.router.post("/login")
        async def login(data: dict):
            username = data.get("username")
            password = data.get("password")
            app_name = data.get("app")
            if not username or not password or not app_name:
                return JSONResponse(
                    content=StatusDTO(
                        status="error",
                        reason="username & password & app required"
                    ).to_dict(),
                    status_code=400
                )
            token = self.service.authenticate_user(username, password, app_name)
            if not token:
                raise HTTPException(status_code=401, detail="Unauthorized")
            return {"token": token, "user": username}

        # GET security config
        @self.router.get("/editor/api/config")
        async def get_security_config():
            try:
                config = self.model.get_security_config()
                return JSONResponse(content=config)
            except Exception as e:
                return JSONResponse(
                    content=StatusDTO(
                        status="error",
                        reason=f"Failed to load: {e}"
                    ).to_dict(),
                    status_code=500
                )

        # POST security config
        @self.router.post("/editor/api/config")
        async def save_security_config(data: dict):
            if not data:
                return JSONResponse(
                    content=StatusDTO(status="error", reason="No data provided").to_dict(),
                    status_code=400
                )
            try:
                self.model.save_security_config(data)
            except Exception as e:
                return JSONResponse(
                    content=StatusDTO(
                        status="error",
                        reason=f"Failed to save: {e}"
                    ).to_dict(),
                    status_code=500
                )
            # Notify service if applicable
            if hasattr(self.service, "notify_config_changed"):
                self.service.notify_config_changed()
            return JSONResponse(content=StatusDTO(status="ok", reason="Config saved").to_dict())

    # ---------------- Helper to register router ----------------
    def register_routes(self, app):
        app.include_router(self.router)