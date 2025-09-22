# communications_service.py
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import CommandFeedbackMsg, SendCommandMsg

class CommandService(BaseService[CommandFeedbackMsg, SendCommandMsg, SendCommandMsg]):
    def __init__(self, event_bus, model, controller):
        super().__init__(event_bus, model, controller, CommandFeedbackMsg, SendCommandMsg, SendCommandMsg)

    def should_accept_update(self, msg: CommandFeedbackMsg) -> bool:
        # Accept all updates by default because this is sent from command executors
        return True