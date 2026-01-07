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
