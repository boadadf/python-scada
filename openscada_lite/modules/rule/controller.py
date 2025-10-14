# communications_controller.py
from openscada_lite.modules.base.base_controller import BaseController

class RuleController(BaseController[None, None]):
    def __init__(self, model, socketio, base_event: str, flask_app=None):
        super().__init__(model, socketio, None, None, base_event=base_event, flask_app=flask_app)

    def validate_request_data(self, data):
        # No validation needed (no U type)
        return data

