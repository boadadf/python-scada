# -----------------------------------------------------------------------------
# Frontend Controller
# -----------------------------------------------------------------------------
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
        @router.get("/frontend/api/tabs")
        async def list_tabs():
            return JSONResponse(content=self.tabs)
