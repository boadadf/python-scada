# communications_controller.py
from typing import Optional
from openscada_lite.frontend.base_controller import BaseController
from openscada_lite.common.models.dtos import DriverConnectStatus, DriverConnectCommand

class CommunicationsController(BaseController[DriverConnectStatus, DriverConnectCommand]):
    def __init__(self, model, socketio):
        super().__init__(model, socketio, DriverConnectStatus, DriverConnectCommand, base_event="driver_connect")

    def validate_incoming_data(self, data: dict) -> Optional[dict]:
        status = data.get("status")
        if status not in ("connect", "disconnect"):
            return {
                "status": "error",
                "reason": "Invalid status. Must be 'connect' or 'disconnect'.",
                "driver_name": data.get("driver_name")
            }
        return None