from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.models.dtos import DataFlowEventMsg, StatusDTO

class TrackingController(BaseController[DataFlowEventMsg, None]):
    def __init__(self, model, socketio, base_event="tracking"):
        # No incoming requests, so use StatusDTO as dummy U_cls
        super().__init__(model, socketio, DataFlowEventMsg, None, base_event=base_event)

    def validate_request_data(self, data):
        # No actions from the view, always return error
        return StatusDTO(status="error", reason="Tracking is read-only.")