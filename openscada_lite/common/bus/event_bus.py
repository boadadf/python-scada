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

import asyncio
from collections import defaultdict
import copy
from typing import Any, Callable, Dict, List

from openscada_lite.common.bus.event_types import EventType

class EventBus:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            raise RuntimeError("Use EventBus.get_instance() instead of direct instantiation.")
        return super().__new__(cls)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            # Temporarily allow instantiation
            cls._instance = super().__new__(cls)
            cls.__init__(cls._instance)
        return cls._instance

    def __init__(self):
        # Each event type has a list of subscriber callbacks
        self._subscribers: Dict[EventType, List[Callable[[Any], Any]]] = defaultdict(list)

    def clear_subscribers(self):
        """Remove all subscribers (for test isolation)."""
        self._subscribers.clear()

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
        to_publish = copy.copy(data)
        """Publish an event to all subscribers asynchronously."""
        for callback in self._subscribers[event_type]:
            await callback(to_publish)