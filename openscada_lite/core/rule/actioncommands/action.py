from abc import ABC, abstractmethod

from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import DTO
from openscada_lite.common.tracking.decorators import publish_data_flow_from_return_async
from openscada_lite.common.tracking.tracking_types import DataFlowStatus

class Action(ABC):

    def __init__(self):
        self.bus = EventBus.get_instance()

    @publish_data_flow_from_return_async(status=DataFlowStatus.CREATED)
    async def __call__(self, datapoint_identifier, params, track_id) -> tuple[DTO, EventType]:
        dto, event = self.get_event_data(datapoint_identifier, params, track_id)
        await self.bus.publish(event, dto)
        return dto, event

    @abstractmethod
    def get_event_data(self, datapoint_identifier, params, track_id) -> tuple[DTO, EventType]:
        pass