# -----------------------------------------------------------------------------
# Copyright 2025 Daniel&Hector Fernandez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

# communications_model.py
import datetime
from typing import Dict
from openscada_lite.common.models.dtos import TagUpdateMsg
from openscada_lite.common.config.config import Config
from openscada_lite.modules.datapoint.utils import Utils
from openscada_lite.modules.base.base_model import BaseModel


class DatapointModel(BaseModel[TagUpdateMsg]):
    """
    Stores the current state of all datapoints as TagUpdateMsg objects.
    """

    def __init__(self):
        super().__init__()
        self._allowed_tags = set(
            Config.get_instance().get_allowed_datapoint_identifiers()
        )
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
                timestamp=now,
            )
