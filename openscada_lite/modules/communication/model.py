# communications_model.py
from openscada_lite.modules.base.base_model import BaseModel
from openscada_lite.common.models.dtos import DriverConnectStatus

class CommunicationModel(BaseModel[DriverConnectStatus]):
    def __init__(self):
        super().__init__()