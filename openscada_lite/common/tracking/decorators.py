# -----------------------------------------------------------------------------
# Copyright 2025 Daniel&Hector Fernandez
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

from functools import wraps
from typing import Any, Awaitable, Callable, Optional

from openscada_lite.common.models.dtos import DataFlowEventMsg
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.tracking.publisher import TrackingPublisher

publisher = TrackingPublisher()

AsyncFunc = Callable[..., Awaitable[Any]]
SyncFunc = Callable[..., Any]
MaybeDTO = Any 


def isValidDTO(obj: Any) -> bool:
    return obj is not None and not isinstance(obj, DataFlowEventMsg)

# 1. Async: DTO as first argument
def publish_data_flow_from_arg_async(status: DataFlowStatus, source: Optional[str] = None):
    def decorator(func: AsyncFunc) -> AsyncFunc:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            result = await func(self, *args, **kwargs)
            event_source = source or self.__class__.__name__
            dto: MaybeDTO = args[0] if args else None
            if isValidDTO(dto):
                publisher.publish_data_flow_event(dto, source=event_source, status=status)
            return result
        return wrapper
    return decorator

# 2. Sync: DTO as first argument
def publish_data_flow_from_arg_sync(status: DataFlowStatus, source: Optional[str] = None):
    def decorator(func: SyncFunc) -> SyncFunc:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            result = func(self, *args, **kwargs)
            event_source = source or self.__class__.__name__
            dto: MaybeDTO = args[0] if args else None
            if isValidDTO(dto):
                # If publisher is async, schedule it
                publisher.publish_data_flow_event(dto, source=event_source, status=status)
            return result
        return wrapper
    return decorator

# 3. Async: DTO as return value (or first of tuple/list)
def publish_data_flow_from_return_async(status: DataFlowStatus, source: Optional[str] = None):
    def decorator(func: AsyncFunc) -> AsyncFunc:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            result = await func(self, *args, **kwargs)
            if isinstance(result, (tuple, list)) and len(result) > 0:
                dto = result[0]
            else:
                dto = result
            event_source = source or self.__class__.__name__
            if isValidDTO(dto):
                publisher.publish_data_flow_event(dto, source=event_source, status=status)
            return result
        return wrapper
    return decorator

# 4. Sync: DTO as return value (or first of tuple/list)
def publish_data_flow_from_return_sync(status: DataFlowStatus, source: Optional[str] = None):
    def decorator(func: SyncFunc) -> SyncFunc:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            result = func(self, *args, **kwargs)
            if isinstance(result, (tuple, list)) and len(result) > 0:
                dto = result[0]
            else:
                dto = result
            event_source = source or self.__class__.__name__
            if isValidDTO(dto):
                publisher.publish_data_flow_event(dto, source=event_source, status=status)
            return result
        return wrapper
    return decorator