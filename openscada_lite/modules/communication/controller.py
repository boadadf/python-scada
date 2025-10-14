# communications_controller.py
from typing import Union, override
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import DriverConnectStatus, DriverConnectCommand, StatusDTO

class CommunicationController(BaseController[DriverConnectStatus, DriverConnectCommand]):
    def __init__(self, model, socketio, base_event="communication", flask_app=None):
        super().__init__(model, socketio, DriverConnectStatus, DriverConnectCommand, base_event=base_event, flask_app=flask_app)

    @override
    def validate_request_data(self, driver_connected_command: DriverConnectCommand) -> Union[DriverConnectCommand, StatusDTO]:
        try:
            status = driver_connected_command.status
            if status not in ("connect", "disconnect", "toggle"):
                return StatusDTO(status="error", reason="Invalid status. Must be 'connect', 'disconnect', or 'toggle'.")
            return driver_connected_command
        except TypeError as e:
            return StatusDTO(status="error", reason='Invalid input data: ' + str(e))