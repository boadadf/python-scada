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

# communications_service.py
from openscada_lite.modules.rule.controller import RuleController
from openscada_lite.modules.rule.model import RuleModel
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import TagUpdateMsg
from openscada_lite.modules.rule.manager.rule_manager import RuleEngine


class RuleService(BaseService[TagUpdateMsg, None, None]):
    def __init__(self, event_bus, model: RuleModel, controller: RuleController):
        super().__init__(event_bus, model, controller, TagUpdateMsg, None, None)
        self.engine = RuleEngine.get_instance(event_bus)

    def should_accept_update(self, msg: TagUpdateMsg) -> bool:
        return True

    async def handle_bus_message(self, msg: TagUpdateMsg):
        # Delegate to RuleEngine's on_tag_update
        await self.engine.on_tag_update(msg)
