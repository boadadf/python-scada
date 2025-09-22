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