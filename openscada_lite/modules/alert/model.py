from openscada_lite.common.models.dtos import ClientAlertMsg
from openscada_lite.modules.base.base_model import BaseModel

class AlertModel(BaseModel[ClientAlertMsg]):
    def __init__(self):
        super().__init__()

    def update(self, msg: ClientAlertMsg):
        """
        Store or update a message.
        """
        # Only store if it's a ClientAlertMsg with alert_type "confirm_cancel"
        from openscada_lite.common.models.dtos import ClientAlertMsg
        if isinstance(msg, ClientAlertMsg):
            if getattr(msg, "alert_type", None) == "confirm_cancel":
                self._store[msg.get_id()] = msg
        else:
            self._store[msg.get_id()] = msg        