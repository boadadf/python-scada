from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type
from openscada_lite.common.models.dtos import DTO
from openscada_lite.modules.base.base_model import BaseModel
from openscada_lite.common.bus.event_bus import EventBus

T = TypeVar('T', bound=DTO)  # From bus
U = TypeVar('U', bound=DTO)  # From controller
V = TypeVar('V', bound=DTO)  # Stored in model and published to view (processed T)
#W = TypeVar('W', bound=DTO)  # Published to bus (processed U)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .base_controller import BaseController

class BaseService(ABC, Generic[T, U, V]):
    """
    Generic service for handling bus messages of type T and controller messages of type U.
    """
    def __init__(self, event_bus: EventBus, model: BaseModel, controller: 'BaseController', T_cls: Type[T], U_cls: Type[U], V_cls: Type[V]=None):
        self.event_bus = event_bus
        self.model = model
        self.controller = controller
        if controller:
            controller.set_service(self)

        # Subscribe to bus for T
        self.event_bus.subscribe(T_cls.get_event_type(), self.handle_bus_message)
        self.T_cls = T_cls
        self.U_cls = U_cls
        self.V_cls = V_cls

    async def handle_bus_message(self, data:T):        
        processed_msg = self.process_msg(data)
        accepted = self.model.update(processed_msg)
        if accepted:
            await self.on_model_accepted_bus_update(processed_msg)
            if self.controller:
                self.controller.publish(processed_msg)

    async def handle_controller_message(self, data:U):
        print("DatapointService.on_model_accepted_bus_update CALLED")
        await self.event_bus.publish(self.U_cls.get_event_type(), data)

    def process_msg(self, msg: T) -> V:
        """
        Convert the incoming bus message to the type the model expects.
        Override in subclass if needed.
        """
        return msg  # Default: no conversion

    async def on_model_accepted_bus_update(self, msg: V):
        """
        Hook for subclasses: called when the model accepts an update.
        Override in subclass if needed.
        """
        pass