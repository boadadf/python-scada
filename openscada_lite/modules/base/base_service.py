# -----------------------------------------------------------------------------
# Copyright 2025 Daniel Fernandez Boada
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic, Type, Union
from openscada_lite.common.tracking.decorators import publish_data_flow_from_arg_async, publish_data_flow_from_return_sync
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.models.dtos import DTO, DataFlowEventMsg
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
    Generic service for handling bus messages of type T (or multiple types) and controller messages of type U.
    """
    def __init__(
        self,
        event_bus: EventBus,
        model: BaseModel,
        controller: 'BaseController',
        T_cls: Union[Type[T], List[Type[T]]],
        U_cls: Type[U],
        V_cls: Type[V] = None
    ):
        self.event_bus = event_bus
        self.model = model
        self.controller = controller
        if controller:
            controller.set_service(self)

        # Support single or multiple T_cls
        if not isinstance(T_cls, list):
            T_cls = [T_cls]
        self.T_cls_list = T_cls
        self.U_cls = U_cls
        self.V_cls = V_cls

        # Subscribe to all event types
        if T_cls is not None:
            for t_cls in self.T_cls_list:
                if t_cls is not None:
                    self.event_bus.subscribe(t_cls.get_event_type(), self.handle_bus_message)

    @publish_data_flow_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def handle_bus_message(self, data:T):
        accept_update = self.should_accept_update(data)
        if not accept_update:
            return
        processed_msg = self.process_msg(data)
        if processed_msg is None:            
            return
        if isinstance(processed_msg, list):
            for msg in processed_msg:
                self.model.update(msg)
                await self.on_model_accepted_bus_update(msg)
                if self.controller:
                    self.controller.publish(msg)
                else:
                    print(f"No controller to publish {msg} to view")
        else:
            self.model.update(processed_msg)
            await self.on_model_accepted_bus_update(processed_msg)
            if self.controller:
                self.controller.publish(processed_msg)
            else:
                print(f"No controller to publish {processed_msg} to view")


    @publish_data_flow_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def handle_controller_message(self, data:U):
        await self.event_bus.publish(self.U_cls.get_event_type(), data)

    @publish_data_flow_from_return_sync(status=DataFlowStatus.CREATED)
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

    @abstractmethod
    def should_accept_update(self, msg: T) -> bool:
        """
        Determine if an incoming message should be accepted.
        Must be implemented by subclasses.
        By default, all messages are accepted.
        """
        pass

    async def async_init(self):
        pass