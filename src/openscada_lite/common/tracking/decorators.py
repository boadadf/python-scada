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
import datetime
from functools import wraps
import json
from typing import Any, Awaitable, Callable, Optional

from fastapi.responses import JSONResponse

from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.models.dtos import DataFlowEventMsg
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.tracking.publisher import TrackingPublisher

import logging

logger = logging.getLogger(__name__)

AsyncFunc = Callable[..., Awaitable[Any]]
SyncFunc = Callable[..., Any]
MaybeDTO = Any


# -----------------------------------------------------------------------------
# Shared internal helpers
# -----------------------------------------------------------------------------


def _extract_dto(result: Any) -> Any:
    """Extract DTO from return values."""
    if isinstance(result, (tuple, list)) and result:
        return result[0]

    if isinstance(result, JSONResponse):
        return result.content

    return result


def _is_valid(dto: Any) -> bool:
    return dto is not None and not isinstance(dto, DataFlowEventMsg)


def _publish(dto: Any, source: str, status: DataFlowStatus):
    pub = TrackingPublisher.get_instance()
    if _is_valid(dto):
        pub.publish_data_flow_event(dto, source, status)


# -----------------------------------------------------------------------------
# INSTANCE FROM DECORATORS (require `self`)
# -----------------------------------------------------------------------------


def publish_from_arg_async(status: DataFlowStatus, source: Optional[str] = None):
    """Async from; DTO is first argument."""

    def decorator(func: AsyncFunc):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            result = await func(self, *args, **kwargs)
            dto = args[0] if args else None
            _publish(dto, source or self.__class__.__name__, status)
            return result

        return wrapper

    return decorator


def publish_from_return_async(status: DataFlowStatus, source: Optional[str] = None):
    """Async from; DTO from return."""

    def decorator(func: AsyncFunc):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            result = await func(self, *args, **kwargs)
            dto = _extract_dto(result)
            _publish(dto, source or self.__class__.__name__, status)
            return result

        return wrapper

    return decorator


def publish_from_arg_sync(status: DataFlowStatus, source: Optional[str] = None):
    def decorator(func: SyncFunc):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            dto = args[0] if args else None
            _publish(dto, source or self.__class__.__name__, status)
            return result

        return wrapper

    return decorator


def publish_from_return_sync(status: DataFlowStatus, source: Optional[str] = None):
    def decorator(func: SyncFunc):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            dto = _extract_dto(result)
            _publish(dto, source or self.__class__.__name__, status)
            return result

        return wrapper

    return decorator


# -----------------------------------------------------------------------------
# FASTAPI ROUTE DECORATORS (NO self — use in controllers)
# -----------------------------------------------------------------------------
def publish_route_async(status: DataFlowStatus, source: Optional[str] = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.debug(f"[TRACKING] Calling {func.__name__}")
            result = await func(*args, **kwargs)

            dto = None
            logger.debug(
                f"[TRACKING] Tape {type(result)} returned from {func.__name__}"
            )
            if isinstance(result, JSONResponse):
                logger.debug(
                    f"[TRACKING] JSONResponse detected with body: {result.body}"
                )
                try:
                    content_dict = json.loads(result.body.decode())
                    dto = DataFlowEventMsg(
                        track_id="N/A",
                        event_type=EventType.USER_ACTION,
                        status=content_dict.get("status", "unknown"),
                        timestamp=datetime.datetime.now(),
                        source=source or func.__name__,
                        payload=content_dict.get("data", None),
                    )
                    logger.debug(f"[TRACKING] Created DataFlowEventMsg: {dto}")
                except Exception as e:
                    logger.debug(f"[TRACKING] Failed to create DataFlowEventMsg: {e}")
            # Only publish if dto is a DataFlowEventMsg
            if isinstance(dto, DataFlowEventMsg):
                pub = TrackingPublisher.get_instance()
                logger.debug(
                    f"[TRACKING] Publishing event from route {func.__name__} with status {status}"
                )
                pub.publish_data_flow_event(
                    dto, source=source or func.__name__, status=status
                )

            return result

        return wrapper

    return decorator
