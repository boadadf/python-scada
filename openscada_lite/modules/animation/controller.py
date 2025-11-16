# -----------------------------------------------------------------------------
# Copyright 2025 Daniel&Hector Fernandez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

from typing import Union
from openscada_lite.common.config.config import Config
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import AlarmUpdateMsg, AnimationUpdateRequestMsg, StatusDTO, AnimationUpdateMsg, TagUpdateMsg

class AnimationController(BaseController[AnimationUpdateMsg, AnimationUpdateRequestMsg]):
    def __init__(self, model, socketio, base_event="animation", flask_app=None):
        super().__init__(model, socketio, AnimationUpdateMsg, AnimationUpdateRequestMsg, base_event=base_event, flask_app=flask_app)
        self.svg_files = Config.get_instance().get_svg_files()

    def register_http(self, flask_app):
        super().register_http(flask_app)
        @flask_app.route("/animation_svgs", methods=["GET"], endpoint="animation_svgs_list")
        def list_svgs():
            from flask import jsonify
            return jsonify(self.svg_files)
    def validate_request_data(self, data:AnimationUpdateRequestMsg) -> AnimationUpdateRequestMsg | StatusDTO:
        return data