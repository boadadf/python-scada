# communications_controller.py
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import CommandFeedbackMsg, SendCommandMsg, StatusDTO

class CommandController(BaseController[CommandFeedbackMsg, SendCommandMsg]):
    def __init__(self, model, socketio, base_event: str, flask_app=None):
        super().__init__(model, socketio, CommandFeedbackMsg, SendCommandMsg, base_event=base_event, flask_app=flask_app)

    def validate_request_data(self, data):
        # Accepts either a dict or a SendCommandMsg
        if isinstance(data, SendCommandMsg):
            return data
        try:
            return SendCommandMsg(**data)
        except Exception as e:
            return StatusDTO(status="error", reason=f"Invalid input data: {e}")
