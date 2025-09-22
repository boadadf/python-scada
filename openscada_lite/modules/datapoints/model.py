# communications_model.py
import datetime
from typing import Dict, override
from openscada_lite.common.models.dtos import TagUpdateMsg
from openscada_lite.common.config.config import Config
from openscada_lite.modules.datapoints.utils import Util
from openscada_lite.modules.base.base_model import BaseModel

class DatapointModel(BaseModel[TagUpdateMsg]):
    """
    Stores the current state of all datapoints as TagUpdateMsg objects.
    """
    def __init__(self):
        super().__init__()
        self._allowed_tags = set(Config.get_instance().get_allowed_datapoint_identifiers())
        self.initial_load()

    def initial_load(self):
        """
        Initializes all allowed tags with value=None, quality='unknown', and current timestamp.
        """
        now = datetime.datetime.now()
        for tag_id in self._allowed_tags:
            self._store[tag_id] = TagUpdateMsg(
                datapoint_identifier=tag_id,
                value=None,
                quality="unknown",
                timestamp=now
            )