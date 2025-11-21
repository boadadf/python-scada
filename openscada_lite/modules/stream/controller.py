# -----------------------------------------------------------------------------
# Stream Controller
# -----------------------------------------------------------------------------
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.config.config import Config


class StreamController(BaseController):
    def __init__(self, model, socketio, module_name: str, router: APIRouter):
        super().__init__(
            model, socketio, None, None, module_name, router
        )
        self.streams = Config.get_instance().get_streams()

    def validate_request_data(self, data):
        return data

    def register_local_routes(self, router: APIRouter):
        @router.get("/streams")
        async def list_streams():
            return JSONResponse(content=self.streams)
