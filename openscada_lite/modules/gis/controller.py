from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import GisUpdateMsg

class GisController(BaseController[GisUpdateMsg, None]):
    def __init__(self, model, socketio, base_event="gis", flask_app=None):
        super().__init__(model, socketio, GisUpdateMsg, None, base_event=base_event, flask_app=flask_app)

    def validate_request_data(self, data):
        return data