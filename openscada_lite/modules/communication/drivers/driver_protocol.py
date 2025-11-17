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

from typing import Protocol, Callable, Any, List
from typing import runtime_checkable

from openscada_lite.common.models.dtos import SendCommandMsg
from openscada_lite.common.models.entities import Datapoint


@runtime_checkable
class DriverProtocol(Protocol):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    def subscribe(self, datapoints: List[Datapoint]) -> None: ...
    def register_value_listener(self, callback: Callable) -> None: ...
    def register_communication_status_listener(self, callback: Callable) -> None: ...
    def register_command_feedback(self, callback: Callable) -> None: ...
    async def send_command(self, data: SendCommandMsg) -> None: ...
    def initialize(self, config: dict) -> None: ...  # <-- NEW

    @property
    def server_name(self) -> str: ...
    @property
    def is_connected(self) -> bool: ...
