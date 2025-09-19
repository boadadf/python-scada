import asyncio
import datetime
from flask_socketio import emit, join_room

import socketio
from openscada_lite.common.models.dtos import TagUpdateMsg
from openscada_lite.frontend.datapoints.model import DatapointModel

class DatapointController:
    def __init__(self, model: DatapointModel, socketio):
        self.model = model
        self.socketio = socketio
        self._initializing_clients = set()
        self.service = None
        self.register_socketio()

    def handle_subscribe_live_feed(self):
        sid = getattr(emit, 'sid', None) or None
        join_room('datapoint_live_feed')
        self._initializing_clients.add(sid)
        all_tags = self.model.get_all_tags()
  
        self.socketio.emit('initial_state', [v.to_dict() for v in all_tags.values()])
        self._initializing_clients.discard(sid)

    def run_async_update(self, tag_id, value, quality, timestamp):
        asyncio.run(self.service.update_tag(tag_id, value, quality, timestamp))

    def handle_set_tag(self, data):
        print(f"Received set_tag request: {data}")
        tag_id = data.get("datapoint_identifier")
        value = data.get("value")
        quality = data.get("quality", "good")
        timestamp = data.get("timestamp")
        if not timestamp:
            timestamp = datetime.datetime.now()
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
            self._initializing_clients.discard(sid)

        @self.socketio.on('set_tag')
        def _handler(data):
            self.handle_set_tag(data)

    def publish_tag(self, tag: TagUpdateMsg):
        try:
            if self._initializing_clients:
                print("Client initializing, skipping live feed publish")
                return

            d = tag.__dict__.copy()
            if "timestamp" in d and d["timestamp"] is not None:
                d["timestamp"] = d["timestamp"].isoformat()

            # Sync emit
            self.socketio.emit('datapoint_update', d, room='datapoint_live_feed')
        except Exception as e:
            print(f"Exception in publish_tag: {e}")
