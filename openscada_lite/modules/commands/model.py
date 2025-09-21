# communications_model.py
from openscada_lite.modules.base.base_model import BaseModel
from openscada_lite.common.models.dtos import CommandFeedbackMsg

class CommunicationsModel(BaseModel[CommandFeedbackMsg]):
    def __init__(self):
        super().__init__()