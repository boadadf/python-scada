# -----------------------------------------------------------------------------
# Stream Service
# -----------------------------------------------------------------------------
from openscada_lite.modules.base.base_service import BaseService

class StreamService(BaseService[
    None, None, None
]):
    def __init__(self, event_bus, model, controller):
        super().__init__(
            event_bus, model, controller,None, None, None
        )

    def should_accept_update(self, msg):
        return False
    