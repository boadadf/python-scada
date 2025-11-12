from flask import jsonify
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import GisUpdateMsg
from openscada_lite.common.config.config import Config

class GisController(BaseController[GisUpdateMsg, None]):
    def __init__(self, model, socketio, base_event="gis", flask_app=None):
        super().__init__(model, socketio, GisUpdateMsg, None, base_event=base_event, flask_app=flask_app)

        if flask_app:
            flask_app.add_url_rule(
                "/api/gis/config", "get_gis_config", self.get_gis_config, methods=["GET"]
            )

    def validate_request_data(self, data):
        return data

    def get_gis_config(self):
        """Expose the GIS configuration from system_config.json."""
        config = Config.get_instance().get_module_config("gis")
        return jsonify(config)