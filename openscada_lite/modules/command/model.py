# -----------------------------------------------------------------------------
# Copyright 2025 Daniel Fernandez Boada
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

from openscada_lite.common.config.config import Config
from openscada_lite.common.models.dtos import CommandFeedbackMsg
from openscada_lite.modules.base.base_model import BaseModel
import datetime

class CommandModel(BaseModel[CommandFeedbackMsg]):
    def __init__(self):
        super().__init__()
        self._allowed_commands = set(Config.get_instance().get_allowed_command_identifiers())
        self.initial_load()

    def initial_load(self):
        now = datetime.datetime.now()
        for cmd_id in self._allowed_commands:
            self._store[cmd_id] = CommandFeedbackMsg(
                command_id="",
                datapoint_identifier=cmd_id,
                value=None,
                feedback=None,
                timestamp=now
            )