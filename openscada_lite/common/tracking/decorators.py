from functools import wraps
from typing import Any, Awaitable, Callable, Optional

from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.tracking.publisher import TrackingPublisher

publisher = TrackingPublisher()

AsyncFunc = Callable[..., Awaitable[Any]]
MaybeDTO = Any  # Replace with your DTO base class if available


def publish_data_flow_from_arg(status: DataFlowStatus, source: Optional[str] = None):
    """Publish a data flow event using the first argument (assumed DTO)."""

    def decorator(func: AsyncFunc) -> AsyncFunc:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            result = await func(self, *args, **kwargs)
            event_source = source or self.__class__.__name__
            dto: MaybeDTO = args[0] if args else None
            if dto is not None:
                await publisher.publish_data_flow_event(dto, source=event_source, status=status)
            return result
        return wrapper

    return decorator


def publish_data_flow_from_return(status: DataFlowStatus, source: Optional[str] = None):
    """Publish a data flow event using the function's return value (event_type, dto)."""

    def decorator(func: AsyncFunc) -> AsyncFunc:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            result = await func(self, *args, **kwargs)
            try:
                event_type, dto = result
            except Exception as e:
                raise ValueError(
                    f"Expected (event_type, dto) return from {func.__name__}, got {result!r}"
                ) from e
            event_source = source or self.__class__.__name__
            if dto is not None:
                await publisher.publish_data_flow_event(dto, source=event_source, status=status)
            return result
        return wrapper

    return decorator
