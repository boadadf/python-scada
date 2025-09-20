# communications_service.py
from openscada_lite.frontend.base_service import BaseService
from openscada_lite.common.models.dtos import DriverConnectStatus, DriverConnectCommand

class CommunicationsService(BaseService[DriverConnectStatus, DriverConnectCommand]):
    def __init__(self, event_bus, model, controller):
        super().__init__(event_bus, model, controller, DriverConnectStatus, DriverConnectCommand)