# -----------------------------------------------------------------------------
# Stream Controller
# -----------------------------------------------------------------------------
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.config.config import Config

class StreamController(BaseController):
    def __init__(self, model, socketio, base_event="stream", flask_app=None):
        super().__init__(model, socketio, None, None, base_event=base_event, flask_app=flask_app)
        self.streams = Config.get_instance().get_streams()

    def validate_request_data(self, data):
        pass

    def register_http(self, flask_app):
        super().register_http(flask_app)
        @flask_app.route("/streams", methods=["GET"], endpoint="streams_list")
        def list_streams():
            from flask import jsonify
            return jsonify(self.streams)