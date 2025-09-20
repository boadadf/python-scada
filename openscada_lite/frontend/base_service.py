# base_service.py
from typing import TypeVar, Generic
from abc import ABC, abstractmethod

from common.models.dtos import DTO
from frontend.base_model import BaseModel

T = TypeVar('T')
U = TypeVar('U')

from typing import TypeVar, Generic, Type
from openscada_lite.common.bus.event_bus import EventBus

T = TypeVar('T', bound=DTO)  # From bus
U = TypeVar('U', bound=DTO)  # From controller

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .base_controller import BaseController

class BaseService(Generic[T, U]):
    """
    Generic service for handling bus messages of type T and controller messages of type U.
    """
    def __init__(self, event_bus: EventBus, model: BaseModel, controller: 'BaseController', T_cls: Type[T], U_cls: Type[U]):
        self.event_bus = event_bus
        self.model = model
        self.controller = controller
        if controller:
            controller.set_service(self)

        # Subscribe to bus for T
        self.event_bus.subscribe(T_cls.get_event_type(), self.on_bus_msg)
        self.T_cls = T_cls
        self.U_cls = U_cls

    async def on_bus_msg(self, data):
        # Convert dict to T if needed
        msg = self.T_cls(**data) if isinstance(data, dict) else data
        self.model.update(msg)
        self.controller.publish(msg)

    async def handle_incoming(self, data):
        # Convert dict to U if needed
        msg = self.U_cls(**data) if isinstance(data, dict) else data
        await self.event_bus.publish(self.U_cls.get_event_type(), msg)
