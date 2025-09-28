# communications_controller.py
import datetime
from typing import Union, override
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import StatusDTO, TagUpdateMsg, RawTagUpdateMsg

class DatapointController(BaseController[TagUpdateMsg, RawTagUpdateMsg]):
    def __init__(self, model, socketio, base_event="datapoint", flask_app=None):
        super().__init__(model, socketio, TagUpdateMsg, RawTagUpdateMsg, base_event=base_event, flask_app=flask_app)

    @override
    def validate_request_data(self, data: RawTagUpdateMsg) -> Union[TagUpdateMsg, StatusDTO]:
        try:
            datapoint_identifier = data.datapoint_identifier
            value = data.value
            if not datapoint_identifier or value is None:
                return StatusDTO(
                    status="error",
                    reason="Missing required fields: 'datapoint_identifier' and 'value' are required."
                )
            if not data.timestamp:
                data.timestamp = datetime.datetime.now()
            return data
        except TypeError as e:
            return StatusDTO(
                status="error",
                reason=f"Invalid input data: {data}"
            )