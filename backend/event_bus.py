import asyncio
from collections import defaultdict
from typing import Any, Callable, Dict, List

class EventBus:
    def __init__(self):
        # Each event type has a list of subscriber callbacks
        self._subscribers: Dict[str, List[Callable[[Any], Any]]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable[[Any], Any]):
        """
        Subscribe a callback to an event type.
        Callback must be async (awaitable).
        """
        if not asyncio.iscoroutinefunction(callback):
            raise ValueError("Subscriber callback must be async")
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Any], Any]):
        """Unsubscribe a callback from an event type."""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    async def publish(self, event_type: str, data: Any):
        """Publish an event to all subscribers asynchronously."""
        tasks = []
        for callback in self._subscribers[event_type]:
            tasks.append(asyncio.create_task(callback(data)))
        if tasks:
            await asyncio.gather(*tasks)

