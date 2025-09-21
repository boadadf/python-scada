# communications_model.py
from openscada_lite.modules.base.base_model import BaseModel
from openscada_lite.common.models.dtos import DriverConnectStatus

class CommunicationsModel(BaseModel[DriverConnectStatus]):
    def get_id(self, msg: DriverConnectStatus) -> str:
        return msg.driver_name