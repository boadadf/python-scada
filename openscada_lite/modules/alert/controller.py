# communications_controller.py
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import ClientAlertFeedbackMsg, ClientAlertMsg

class AlertController(BaseController[ClientAlertMsg, ClientAlertFeedbackMsg]):
    def __init__(self, model, socketio, base_event: str, flask_app=None):
        super().__init__(model, socketio, ClientAlertMsg, ClientAlertFeedbackMsg, base_event=base_event, flask_app=flask_app)

    def validate_request_data(self, data: ClientAlertMsg):
            return data