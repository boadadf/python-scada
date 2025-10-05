import os
from openscada_lite.common.config.config import Config
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import AnimationUpdateRequestMsg, StatusDTO, AnimationUpdateMsg

class AnimationController(BaseController[AnimationUpdateMsg, AnimationUpdateRequestMsg]):
    def __init__(self, model, socketio, base_event="animation", flask_app=None):
        super().__init__(model, socketio, AnimationUpdateMsg, AnimationUpdateRequestMsg, base_event=base_event, flask_app=flask_app)
        self.svg_files = Config.get_instance().get_svg_files()

    def register_http(self, flask_app):
        @flask_app.route("/animation_svgs", methods=["GET"], endpoint="animation_svgs_list")
        def list_svgs():
            from flask import jsonify
            return jsonify(self.svg_files)

    def validate_request_data(self, data):
        return StatusDTO(status="error", reason="No incoming HTTP data allowed")
