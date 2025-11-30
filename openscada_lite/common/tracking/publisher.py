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
import json
import threading
import asyncio
import queue
from typing import Optional

from openscada_lite.common.tracking.utils import safe_serialize
from openscada_lite.common.bus.event_bus import EventBus, EventType
from openscada_lite.common.config.config import Config
from openscada_lite.common.models.dtos import DTO, DataFlowEventMsg
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
import logging

logger = logging.getLogger(__name__)


class TrackingPublisher:
    """
    Robust publisher:

    - Buffers events while disabled / loop not ready.
    - When enabled, schedules coroutines onto the provided loop (fire-and-forget).
    - Does not block the caller or worker thread waiting for loop tasks.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    @classmethod
    def get_instance(cls) -> "TrackingPublisher":
        return cls()

    def __init__(self):
        if getattr(self, "_constructed", False):
            return
        self._constructed = True

        # config defaults (may be updated in initialize)
        config = Config.get_instance()
        tracking_cfg = config.get_module_config("tracking") or {}
        self.mode = tracking_cfg.get("mode")
        self.file_path = tracking_cfg.get("file_path", "flow_events.log")

        # runtime
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._enabled = False  # only publish when enabled
        self.queue: "queue.Queue[Optional[DataFlowEventMsg]]" = queue.Queue()
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

    def initialize(self, loop: asyncio.AbstractEventLoop):
        """
        Set the loop; does NOT automatically enable publishing.
        Call `enable()` when you want the publisher to start draining/dispatching events.
        """
        self.loop = loop
        logging.debug("[TrackingPublisher] loop injected: %s", loop)

        # Ensure worker thread running
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._worker_thread = threading.Thread(
                target=self._worker, name="TrackingPublisherWorker", daemon=True
            )
            self._worker_thread.start()
            logger.debug("[TrackingPublisher] worker thread started")

    def enable(self):
        """Enable actual deliveries to the event loop."""
        """Safe to call once the app is fully running."""
        self._enabled = True
        logger.debug("[TrackingPublisher] enabled; will start dispatching queued events")

    def disable(self):
        self._enabled = False
        logger.debug("[TrackingPublisher] disabled; will buffer events")

    def publish_data_flow_event(self, dto: DTO, source: str, status: DataFlowStatus):
        logging.debug("[TrackingPublisher] publish_data_flow_event called")
        logging.debug(f"[TrackingPublisher] preparing to create event for {dto}")
        if self.mode == "none" or dto is None:
            return
        # If already a DataFlowEventMsg, just queue it
        if isinstance(dto, DataFlowEventMsg):
            event = dto
        # Only create a new event if dto is a valid DTO (has get_track_payload)
        elif hasattr(dto, "get_track_payload") and callable(dto.get_track_payload):
            try:
                event = DataFlowEventMsg(
                    track_id=getattr(dto, "track_id", ""),
                    event_type=dto.__class__.__name__,
                    source=source,
                    status=status,
                    timestamp=datetime.datetime.now(),
                    payload=dto.get_track_payload(),
                )
            except Exception as e:
                logging.debug("[TrackingPublisher] failed creating DataFlowEventMsg: %s", e)
                return
        else:
            logging.debug("[TrackingPublisher] skipped: dto is not a valid DTO or DataFlowEventMsg")
            return
        logging.debug("[TrackingPublisher] created event %s %s", event.track_id, status)
        self.queue.put(event)
        logging.debug("[TrackingPublisher] queued event %s %s", event.track_id, status)

    def _is_ready_to_publish(self) -> bool:
        """Check if the publisher is ready to publish events."""
        return (
            self._enabled
            and self.loop is not None
            and getattr(self.loop, "is_running", lambda: False)()
        )

    def _requeue_event(self, item: DataFlowEventMsg):
        """Requeue an event when not ready to publish."""
        logging.debug(
            "[TrackingPublisher] not enabled or loop not ready, requeuing event %s",
            item.track_id,
        )
        try:
            self.queue.put(item)
        except Exception:
            logger.exception("[TrackingPublisher] failed to requeue event")
        self._stop_event.wait(0.2)

    def _publish_to_event_bus(self, item: DataFlowEventMsg):
        """Publish event to the event bus."""
        try:
            logging.debug("[TrackingPublisher] scheduling publish for %s", item.track_id)
            asyncio.run_coroutine_threadsafe(
                EventBus.get_instance().publish(EventType.TRACKING_EVENT, item),
                self.loop,
            )
        except Exception:
            logger.exception("[TrackingPublisher] failed scheduling publish for event")

    def _persist_to_file(self, item: DataFlowEventMsg):
        """Persist event to file if mode is 'file'."""
        if self.mode == "file":
            try:
                with open(self.file_path, "a") as f:
                    f.write(json.dumps(item.get_track_payload(), default=safe_serialize) + "\n")
            except Exception:
                logger.exception("[TrackingPublisher] failed writing event to file")

    def _worker(self):
        """Background worker that drains buffer and attempts delivery when enabled."""
        logging.debug("[TrackingPublisher] worker started, waiting for events...")
        while not self._stop_event.is_set():
            try:
                item = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            logging.debug("[TrackingPublisher] worker got item from queue: %s", item)

            if item is None:
                logger.debug("[TrackingPublisher] worker received shutdown sentinel")
                break

            if not self._is_ready_to_publish():
                self._requeue_event(item)
                continue

            self._publish_to_event_bus(item)
            self._persist_to_file(item)

        logger.debug("[TrackingPublisher] worker exiting")

    def shutdown(self, timeout: float = 2.0):
        self._stop_event.set()
        # wake worker
        try:
            self.queue.put_nowait(None)
        except Exception:
            pass
        if self._worker_thread:
            self._worker_thread.join(timeout=timeout)
        logger.debug("[TrackingPublisher] shutdown complete")
