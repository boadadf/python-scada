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
