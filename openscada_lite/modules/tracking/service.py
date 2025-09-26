from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import DataFlowEventMsg, StatusDTO

class TrackingService(BaseService[DataFlowEventMsg, None, DataFlowEventMsg]):
    def __init__(self, event_bus, model, controller):
        super().__init__(event_bus, model, controller, DataFlowEventMsg, None, DataFlowEventMsg)

    def should_accept_update(self, msg: DataFlowEventMsg) -> bool:
        return True