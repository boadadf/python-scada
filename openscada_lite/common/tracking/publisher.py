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
from openscada_lite.common.tracking.utils import safe_serialize
from openscada_lite.common.bus.event_bus import EventBus, EventType
from openscada_lite.common.config.config import Config
from openscada_lite.common.models.dtos import DTO, DataFlowEventMsg
from openscada_lite.common.tracking.tracking_types import DataFlowStatus


class TrackingPublisher:
    def __init__(self):
        config = Config.get_instance()
        tracking_cfg = config.get_module_config("tracking")
        self.mode = tracking_cfg.get("mode", "none")
        self.file_path = tracking_cfg.get("file_path", "flow_events.log")
        # Use a queue and a single background worker thread to efficiently handle
        # all tracking events.
        # This avoids spawning a new thread per event and prevents blocking the main application.
        self.queue = queue.Queue()
        threading.Thread(target=self.worker, daemon=True).start()

    def publish_data_flow_event(self, dto: DTO, source: str, status: DataFlowStatus):
        """
        Synchronously enqueue a tracking event for background processing.
        This method is safe to call from any thread or async context and returns immediately.
        The actual event bus publishing and file writing are handled in the
        background worker thread.
        """
        if self.mode == "none" or dto is None or not hasattr(dto, "track_id"):
            return
        flow_event = DataFlowEventMsg(
            track_id=dto.track_id,
            event_type=dto.__class__.__name__,
            source=source,
            status=status,
            timestamp=datetime.datetime.now(),
            payload=dto.get_track_payload(),
        )
        self.queue.put(flow_event)

    def worker(self):
        """
        Background worker thread that processes the event queue.
        For each event, it publishes to the event bus and writes to file if enabled.
        """
        while True:
            flow_event = self.queue.get()
            self.thread_job(flow_event)
            self.queue.task_done()

    def _run_in_thread(self, flow_event: DataFlowEventMsg):
        # Legacy: not used with the queue/worker pattern, but kept for compatibility.
        threading.Thread(
            target=self.thread_job, args=(flow_event,), daemon=True
        ).start()

    def thread_job(self, flow_event: DataFlowEventMsg):
        """
        Handles the actual publishing and file writing for a single event.
        Runs in the background worker thread.
        """
        # Publish to event bus (async, so we use asyncio.run in this thread)
        asyncio.run(EventBus.get_instance().publish(EventType.FLOW_EVENT, flow_event))
        if self.mode == "file":
            with open(self.file_path, "a") as f:
                f.write(
                    json.dumps(flow_event.get_track_payload(), default=safe_serialize)
                    + "\n"
                )
