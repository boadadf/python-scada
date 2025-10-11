# base_controller.py
from abc import ABC, abstractmethod
import asyncio
from typing import Generic, TypeVar, Optional, Type, TYPE_CHECKING, Union
from flask import request, jsonify
from flask_socketio import SocketIO, join_room, emit

from openscada_lite.common.tracking.decorators import publish_data_flow_from_arg_sync
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.models.dtos import StatusDTO
from openscada_lite.modules.base.base_model import BaseModel
from openscada_lite.modules.base.base_service import BaseService

T = TypeVar("T")  # Outgoing message type (to client)
U = TypeVar("U")  # Request data type (from client)

if TYPE_CHECKING:
    from .base_service import BaseService


class BaseController(ABC, Generic[T, U]):
    """
    Generic controller for handling frontend-backend communication:
      - WebSocket (subscribe/publish)
      - HTTP POST (send commands)
    """

    service: Optional["BaseService[T, U]"]

    def __init__(
        self,
        model: BaseModel,
        socketio: SocketIO,
        T_cls: Type[T],
        U_cls: Optional[Type[U]],
        base_event: str,
        room: str = None,
        flask_app=None,
    ):
        self.model = model
        self.socketio = socketio
        self.T_cls = T_cls
        self.U_cls = U_cls
        self.base_event = base_event
        self.room = room or f"{base_event}_room"
        self.service = None
        self._initializing_clients = set()
        self.flask_app = flask_app
        # Register websocket and HTTP handlers
        self.register_socketio()
        if flask_app is not None:
            self.register_http(flask_app)

    def set_service(self, service: BaseService):
        self.service = service

    # ---------------------------------------------------------------------
    # WebSocket (for live feed only)
    # ---------------------------------------------------------------------
    def register_socketio(self):
        @self.socketio.on(f"{self.base_event}_subscribe_live_feed")
        def _subscribe_handler():
            self.handle_subscribe_live_feed()

    def handle_subscribe_live_feed(self):
        """Adds the client to the room and sends all current T messages."""
        sid = getattr(emit, "sid", None) or None
        join_room(self.room)
        self._initializing_clients.add(sid)

        all_msgs = self.model.get_all()
        sorted_msgs = sorted(all_msgs.values(), key=lambda v: v.get_id())
        self.socketio.emit(
            f"{self.base_event}_initial_state",
            [v.to_dict() for v in sorted_msgs],
            room=self.room,
        )
        self._initializing_clients.discard(sid)

    @publish_data_flow_from_arg_sync(status=DataFlowStatus.FORWARDED)
    def publish(self, msg: T):
        """Publishes a T message to all subscribed clients in the room."""
        if self._initializing_clients:
            return  # Prevent flooding while initializing
        self.socketio.emit(
            f"{self.base_event}_{self.T_cls.__name__.lower()}",
            msg.to_dict(),
            room=self.room,
        )

    # ---------------------------------------------------------------------
    # HTTP (for send_* endpoints)
    # ---------------------------------------------------------------------
    def register_http(self, flask_app):        
        if self.U_cls is None:
            return

        endpoint_name = f"{self.base_event}_send_{self.U_cls.__name__.lower()}"
        route_path = f"/{endpoint_name}"
        print(f"Registering HTTP POST endpoint: {route_path}")
        @flask_app.route(route_path, methods=["POST"], endpoint=endpoint_name)
        def _incoming_handler():
            data = request.get_json() or {}
            username = request.headers.get("X-User", "")  # Injected by login/session

            if not self.is_allowed(username, endpoint_name):
                return jsonify(StatusDTO(status="error", reason="Unauthorized").to_dict()), 403

            return self.handle_request(data)

    def handle_request(self, data):
        """Validate and forward incoming request to the service."""
        obj_data = self.U_cls(**data) if isinstance(data, dict) else data
        result = self.validate_request_data(obj_data)

        if isinstance(result, StatusDTO):
            return jsonify(result.to_dict()), 400

        if self.service:
            asyncio.run(self.service.handle_controller_message(result))

        return jsonify(StatusDTO(status="ok", reason="Request accepted.").to_dict()), 200

    # ---------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------
    @abstractmethod
    def validate_request_data(self, data: U) -> Union[U, StatusDTO]:
        """Validate incoming data. Return U if valid, or a StatusDTO with error details if invalid."""
        pass

    # ---------------------------------------------------------------------
    # Security
    # ---------------------------------------------------------------------
    @classmethod
    def is_allowed(cls, username: str, endpoint_name: str) -> bool:
        return True
        """ try:
            from openscada_lite.modules.security.service import SecurityService

            service: SecurityService = SecurityService.get_instance()
            if service:
                return service.is_allowed(username, endpoint_name)
            return True
        except ImportError:
            # Security module not present → allow everything
            return True
        except Exception:
            # Fail-safe → deny if security exists but errors
            return False """
