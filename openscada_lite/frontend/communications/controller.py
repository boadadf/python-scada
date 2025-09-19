from threading import Lock
from flask_socketio import emit, join_room

class CommunicationsController:
    def __init__(self, model, socketio):
        self.model = model
        self.socketio = socketio
        self._lock = Lock()
        self._initializing_clients = set()
        self.service = None
        self.register_socketio()

    def handle_subscribe_driver_status(self):
        sid = getattr(emit, 'sid', None) or None
        join_room('driver_status_room')
        with self._lock:
            self._initializing_clients.add(sid)
        all_status = self.model.get_all_status()
        self.socketio.emit('driver_status_all', all_status, room='driver_status_room')
        with self._lock:
            self._initializing_clients.discard(sid)

    def register_socketio(self):
        @self.socketio.on("connect_driver")
        def handle_connect_driver(data):
            status = data.get("status")
            server_name = data.get("driver_name")
            if status not in ("connect", "disconnect"):
                self.socketio.emit(
                    "connect_driver_ack",
                    {
                        "status": "error",
                        "reason": "Invalid status. Must be 'connect' or 'disconnect'.",
                        "driver_name": data.get("driver_name")
                    }
                )
                return
            import asyncio
            asyncio.run(self.service.send_connect_status(data["driver_name"], status))
            self.socketio.emit(
                "connect_driver_ack",
                {"status": "ok", "driver_name": data["driver_name"]}
            )

        @self.socketio.on("subscribe_driver_status")
        def _handler():
            self.handle_subscribe_driver_status()

        @self.socketio.on("disconnect")
        def handle_disconnect():
            sid = getattr(emit, 'sid', None) or None
            with self._lock:
                self._initializing_clients.discard(sid)

    def publish_status(self, driver_name, status):
        # Block if any client is currently receiving initial state
        with self._lock:
            if self._initializing_clients:
                return
        self.socketio.emit("driver_status_update", {"driver_name": driver_name, "status": status}, room="driver_status_room")