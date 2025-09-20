# base_controller.py
from typing import Generic, TypeVar, Optional, Type, TYPE_CHECKING
from flask_socketio import SocketIO, join_room, emit
from openscada_lite.frontend.base_model import BaseModel
from openscada_lite.frontend.base_service import BaseService

T = TypeVar('T')  # Outgoing message type (to client)
U = TypeVar('U')  # Incoming message type (from client)

if TYPE_CHECKING:
    from .base_service import BaseService

class BaseController(Generic[T, U]):
    """
    Generic controller for handling frontend-backend communication with room support.
    """

    service: Optional['BaseService[T, U]']

    def __init__(self, model: BaseModel, socketio: SocketIO, T_cls: Type[T], U_cls: Type[U], base_event: str, room: str = None):
        self.model = model
        self.socketio = socketio
        self.T_cls = T_cls
        self.U_cls = U_cls
        self.base_event = base_event
        self.room = room or f"{base_event}_room"
        self.service = None
        self._initializing_clients = set()
        self.register_socketio()

    def set_service(self, service: BaseService):
        self.service = service

    def register_socketio(self):
        @self.socketio.on(f'{self.base_event}_subscribe_live_feed')
        def _subscribe_handler():
            self.handle_subscribe_live_feed()

        @self.socketio.on(f'{self.base_event}_send_{self.U_cls.__name__.lower()}')
        def _incoming_handler(data):
            error = self.validate_incoming_data(data)
            if error:
                self.socketio.emit(f'{self.base_event}_ack', error)
                return
            if self.service:
                self.socketio.start_background_task(self.service.handle_incoming, data)
            self.socketio.emit(
                f'{self.base_event}_ack',
                {"status": "ok"}
            )
           
           
    def handle_subscribe_live_feed(self):
        """
        Adds the client to the room and sends all current T messages.
        """
        sid = getattr(emit, 'sid', None) or None
        join_room(self.room)
        self._initializing_clients.add(sid)
        all_msgs = self.model.get_all()
        self.socketio.emit(
            f'{self.base_event}_initial_state',
            [v.to_dict() for v in all_msgs.values()],
            room=self.room
        )
        self._initializing_clients.discard(sid)

    def publish(self, msg: T):
        """
        Publishes a T message to all subscribed clients in the room.
        """
        # Optionally block if initializing clients (like your old code)
        if self._initializing_clients:
            return
        self.socketio.emit(
            f'{self.base_event}_{self.T_cls.__name__.lower()}',
            msg.to_dict(),
            room=self.room
        )

    def validate_incoming_data(self, data: dict) -> Optional[dict]:
        """
        Validate incoming data from the client.
        Return an error dict to emit if invalid, or None if valid.
        Override in concrete controllers.
        """
        return None        