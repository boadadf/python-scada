# communications_service.py
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import DriverConnectStatus, DriverConnectCommand

class CommunicationService(BaseService[DriverConnectStatus, DriverConnectCommand, DriverConnectCommand]):
    def __init__(self, event_bus, model, controller):
        super().__init__(event_bus, model, controller, DriverConnectStatus, DriverConnectCommand, DriverConnectCommand)

    def should_accept_update(self, msg: DriverConnectStatus) -> bool:
        # Accept all updates by default because this is sent from drivers
        return True