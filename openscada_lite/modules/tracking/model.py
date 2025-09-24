from openscada_lite.common.models.dtos import DataFlowEventMsg
from openscada_lite.modules.base.base_model import BaseModel

class TrackingModel(BaseModel[DataFlowEventMsg]):
    def __init__(self):
        super().__init__()