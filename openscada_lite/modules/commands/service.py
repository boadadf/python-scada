# communications_service.py
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import CommandFeedbackMsg, SendCommandMsg

class CommunicationsService(BaseService[CommandFeedbackMsg, SendCommandMsg, SendCommandMsg]):
    def __init__(self, event_bus, model, controller):
        super().__init__(event_bus, model, controller, CommandFeedbackMsg, SendCommandMsg, SendCommandMsg)