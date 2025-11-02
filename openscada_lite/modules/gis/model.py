from openscada_lite.modules.base.base_model import BaseModel
from openscada_lite.common.models.dtos import GisUpdateMsg

class GisModel(BaseModel[GisUpdateMsg]):
    def __init__(self):
        super().__init__()