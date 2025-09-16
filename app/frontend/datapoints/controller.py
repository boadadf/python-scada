import asyncio
from datetime import datetime, timezone
from flask_socketio import emit, join_room
from threading import Lock

import socketio
from app.common.models.dtos import TagUpdateMsg
from app.frontend.datapoints.model import DatapointModel

class DatapointController:
    def __init__(self, model: DatapointModel, socketio):
        self.model = model
        self.socketio = socketio
        self._initializing_clients = set()
        self._lock = Lock()
        self.service = None
        self.register_socketio()

    def handle_subscribe_live_feed(self):
        sid = getattr(emit, 'sid', None) or None
        join_room('datapoint_live_feed')
        with self._lock:
            self._initializing_clients.add(sid)
        all_tags = self.model.get_all_tags()
        self.socketio.emit('initial_state', [v.__dict__ for v in all_tags.values()])
        with self._lock:
            self._initializing_clients.discard(sid)

    def run_async_update(self, tag_id, value, quality, timestamp):
        asyncio.run(self.service.update_tag(tag_id, value, quality, timestamp))

    def handle_set_tag(self, data):
        tag_id = data.get("datapoint_identifier")
        value = data.get("value")
        quality = data.get("quality", "good")
        timestamp = data.get("timestamp")
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()
        if self.service:
            if hasattr(self.service, "update_tag") and callable(self.service.update_tag):
                # Run the async update_tag in the background
                self.socketio.start_background_task(self.run_async_update, tag_id, value, quality, timestamp)
                self.socketio.emit('set_tag_ack', {"status": "ok", "datapoint_identifier": tag_id})
            else:
                self.socketio.emit('set_tag_ack', {"status": "error", "reason": "Service missing update_tag"})
        else:
            self.socketio.emit('set_tag_ack', {"status": "error", "reason": "No service attached"})

    def register_socketio(self):
        @self.socketio.on('subscribe_live_feed')
        def _handler():
            self.handle_subscribe_live_feed()

        @self.socketio.on('disconnect')
        def handle_disconnect():
            sid = getattr(socketio, 'sid', None) or getattr(emit, 'sid', None) or None
            with self._lock:
                self._initializing_clients.discard(sid)

        @self.socketio.on('set_tag')
        def _handler(data):
            self.handle_set_tag(data)

    def publish_tag(self, tag: TagUpdateMsg):
        # Block if any client is currently receiving initial state
        with self._lock:
            if self._initializing_clients:
                return  # Optionally, queue updates if you want to send them after init
        self.socketio.emit('datapoint_update', tag.__dict__, room='datapoint_live_feed')