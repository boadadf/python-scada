from openscada_lite.modules.base.base_model import BaseModel

class RuleModel(BaseModel[None]):
    def __init__(self):
        super().__init__()
        # Optionally: self.rule_states = {}  # For future rule state tracking