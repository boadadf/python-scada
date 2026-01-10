from fastapi import APIRouter
from openscada_lite.modules.base.base_controller import BaseController

class ScheduleController(BaseController[None, None]):
    def __init__(self, model, socketio, module_name: str, router: APIRouter):
        super().__init__(model, socketio, None, None, module_name, router)

    def validate_request_data(self, data: None) -> None:
        return data
