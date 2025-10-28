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

from typing import Protocol
from openscada_lite.common.models.dtos import RawTagUpdateMsg, CommandFeedbackMsg, DriverConnectStatus

class CommunicationListener(Protocol):
    async def on_raw_tag_update(self, msg: RawTagUpdateMsg): ...
    async def on_command_feedback(self, msg: CommandFeedbackMsg): ...
    async def on_driver_connect_status(self, msg: DriverConnectStatus): ...