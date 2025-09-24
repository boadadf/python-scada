from openscada_lite.modules.base.base_model import BaseModel
from openscada_lite.common.models.dtos import AlarmUpdateMsg

class AlarmModel(BaseModel[AlarmUpdateMsg]):
    def __init__(self):
        super().__init__()

    def update(self, msg: AlarmUpdateMsg):
        """
        Store or update a message.
        """
        if msg.isFinished():
            # If the alarm is finished (deactivated and acknowledged), remove it from the store
            if msg.get_id() in self._store:
                del self._store[msg.get_id()]
        else:
            self._store[msg.get_id()] = msg  