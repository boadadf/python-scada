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

# communications_controller.py
import datetime
from typing import Union
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import StatusDTO, TagUpdateMsg, RawTagUpdateMsg


class DatapointController(BaseController[TagUpdateMsg, RawTagUpdateMsg]):
    def __init__(self, model, socketio, base_event="datapoint"):
        super().__init__(
            model,
            socketio,
            TagUpdateMsg,
            RawTagUpdateMsg,
            base_event=base_event,
        )

    def validate_request_data(
        self, data: RawTagUpdateMsg
    ) -> Union[TagUpdateMsg, StatusDTO]:
        try:
            datapoint_identifier = data.datapoint_identifier
            value = data.value
            if not datapoint_identifier or value is None:
                return StatusDTO(
                    status="error",
                    reason="Missing required fields: 'datapoint_identifier'"
                    " and 'value' are required.",
                )
            if not data.timestamp:
                data.timestamp = datetime.datetime.now()
            return data
        except TypeError:
            return StatusDTO(status="error", reason=f"Invalid input data: {data}")
