import asyncio
from collections import defaultdict
from typing import Any, Callable, Dict, List

from openscada_lite.common.bus.event_types import EventType

class EventBus:
    def __init__(self):
        # Each event type has a list of subscriber callbacks
        self._subscribers: Dict[EventType, List[Callable[[Any], Any]]] = defaultdict(list)

    def subscribe(self, event_type: EventType, callback: Callable[[Any], Any]):
        """
        Subscribe a callback to an event type.
        Callback must be async (awaitable).
        """
        if not asyncio.iscoroutinefunction(callback):
            raise ValueError("Subscriber callback must be async")
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable[[Any], Any]):
        """Unsubscribe a callback from an event type."""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    async def publish(self, event_type: EventType, data: Any):
        """Publish an event to all subscribers asynchronously."""
        tasks = []
        for callback in self._subscribers[event_type]:
            await callback(data)

