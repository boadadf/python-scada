from collections import OrderedDict
from openscada_lite.common.models.dtos import DataFlowEventMsg
from openscada_lite.modules.base.base_model import BaseModel

class TrackingModel(BaseModel[DataFlowEventMsg]):
    MAX_ENTRIES = 100

    def __init__(self):
        # Use OrderedDict to maintain insertion order for rotation
        self._store = OrderedDict()

    def update(self, msg: DataFlowEventMsg):
        """
        Store or update a message, keeping only the last MAX_ENTRIES.
        """
        msg_id = msg.get_id()
        if msg_id in self._store:
            self._store.pop(msg_id)
        self._store[msg_id] = msg
        # Remove oldest if over limit
        while len(self._store) > self.MAX_ENTRIES:
            self._store.popitem(last=False)