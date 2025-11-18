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
from abc import ABC, abstractmethod
import asyncio
import threading
from typing import Generic, TypeVar, Optional, Type, Union
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from socketio import AsyncServer
from openscada_lite.modules.security.service import SecurityService
from openscada_lite.modules.base.base_model import BaseModel
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import StatusDTO
from openscada_lite.common.tracking.decorators import publish_data_flow_from_arg_sync
from openscada_lite.common.tracking.tracking_types import DataFlowStatus

T = TypeVar("T")  # Outgoing message type (to client)
U = TypeVar("U")  # Request data type (from client)


class BaseController(ABC, Generic[T, U]):
    """
    Generic controller for FastAPI + Socket.IO:
      - WebSocket (subscribe/publish)
      - HTTP POST endpoints via APIRouter
      - Batch publishing (async-safe)
    """
    service: Optional["BaseService[T, U]"]

    def __init__(
        self,
        model: BaseModel,
        socketio: AsyncServer,
        T_cls: Type[T],
        U_cls: Optional[Type[U]],
        base_event: str,
        room: Optional[str] = None,
        batch_interval: float = 1.0,  # seconds
    ):
        self.model = model
        self.socketio = socketio
        self.T_cls = T_cls
        self.U_cls = U_cls
        self.base_event = base_event
        self.room = room or f"{base_event}_room"
        self.service = None
        self._initializing_clients = set()

        # --- Async batching ---
        self._batch_buffer = []
        self._batch_lock = threading.Lock()
        self._batch_interval = batch_interval
        self._batch_task_started = False

        # HTTP router container
        self.router: Optional[APIRouter] = None

        # Register WebSocket events
        self.register_socketio()

    def set_service(self, service: "BaseService"):
        self.service = service

    def get_router(self) -> APIRouter:
        return self.router
    
    # ---------------------------------------------------------------------
    # WebSocket handling
    # ---------------------------------------------------------------------
    def register_socketio(self):
        @self.socketio.on(f"{self.base_event}_subscribe_live_feed")
        async def _subscribe_handler(sid):
            await self.handle_subscribe_live_feed(sid)

    async def handle_subscribe_live_feed(self, sid):
        print(f"[{self.base_event}] ******* Client subscribed to live feed: {sid}")
        self._initializing_clients.add(sid)
        all_msgs = self.model.get_all()
        sorted_msgs = sorted(all_msgs.values(), key=lambda v: v.get_id())
        print(f"[{self.base_event}] Sending initial state to {self.base_event}, {len(sorted_msgs)} items.")
        await self.socketio.enter_room(sid, self.room)
        await self.socketio.emit(
            f"{self.base_event}_initial_state",
            [v.to_dict() for v in sorted_msgs],
            room=self.room,
        )
        self._initializing_clients.discard(sid)

    @publish_data_flow_from_arg_sync(status=DataFlowStatus.FORWARDED)
    def publish(self, msg: T):
        """Buffer messages to be sent in batch."""
        if self._initializing_clients:
            return
        with self._batch_lock:
            self._batch_buffer.append(msg.to_dict())
        if not self._batch_task_started:
            self._start_batch_task()

    def _start_batch_task(self):
        """Schedule async batch emitter in event loop."""
        loop = asyncio.get_event_loop()
        loop.create_task(self._batch_worker())
        self._batch_task_started = True

    async def _batch_worker(self):
        while True:
            await asyncio.sleep(self._batch_interval)
            buffer_copy = []
            with self._batch_lock:
                if self._batch_buffer:
                    buffer_copy = self._batch_buffer.copy()
                    self._batch_buffer.clear()
            if buffer_copy:
                await self.socketio.emit(
                    f"{self.base_event}_{self.T_cls.__name__.lower()}",
                    buffer_copy,
                    room=self.room,
                )

    # ---------------------------------------------------------------------
    # HTTP endpoints via APIRouter
    # ---------------------------------------------------------------------
    def register_routes(self, router: APIRouter):
        self.router = router
        if self.U_cls is None:
            return

        endpoint_name = f"{self.base_event}_send_{self.U_cls.__name__.lower()}"
        route_path = f"/{endpoint_name}"

        @router.post(route_path, name=endpoint_name)
        async def _incoming_handler(request: Request):
            data = await request.json()
            obj_data = self.U_cls(**data) if isinstance(data, dict) else data
            result = self.validate_request_data(obj_data)
            if isinstance(result, StatusDTO):
                return JSONResponse(status_code=400, content=result.to_dict())
            if self.service:
                await self.service.handle_controller_message(result)
            return JSONResponse(
                content=StatusDTO(status="ok", reason="Request accepted.").to_dict()
            )

    # ---------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------
    @abstractmethod
    def validate_request_data(self, data: U) -> Union[U, StatusDTO]:
        """Return validated data or StatusDTO for errors."""
        pass

    # ---------------------------------------------------------------------
    # Security hook
    # ---------------------------------------------------------------------
    @classmethod
    def is_allowed(cls, username: str, endpoint_name: str) -> bool:
        return SecurityService.get_instance_or_none().is_user_allowed_for_endpoint(username, endpoint_name)