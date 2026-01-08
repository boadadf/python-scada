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
from socketio import AsyncServer
from openscada_lite.modules.security.service import SecurityService
from openscada_lite.modules.base.base_model import BaseModel
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import StatusDTO
from openscada_lite.common.tracking.decorators import (
    publish_from_arg_sync,
    publish_route_async,
)
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.utils.SecurityUtils import verify_jwt
from openscada_lite.common.utils.ResponseUtils import make_response

import logging

logger = logging.getLogger(__name__)

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
        t_cls: Type[T],
        u_cls: Optional[Type[U]],
        base_event: str,
        router: APIRouter,
        batch_interval: float = 1.0,  # seconds
    ):
        self.model = model
        self.socketio = socketio
        self.t_cls = t_cls
        self.u_cls = u_cls
        self.base_event = base_event
        self.room = f"{base_event}_room"
        self.service = None
        self.router = router
        self._initializing_clients = set()

        # --- Async batching ---
        self._batch_buffer = []
        self._batch_lock = threading.Lock()
        self._batch_interval = batch_interval
        self._batch_task_started = False

        # Register WebSocket events
        self.register_socketio()
        # Create FastAPI router for HTTP endpoints
        self._register_generic_routes(u_cls)
        self.register_local_routes(router)

    def register_local_routes(self, router: APIRouter):
        """Register module-specific FastAPI routes. To be overridden by subclasses."""
        pass

    def set_service(self, service: "BaseService"):
        self.service = service

    # ---------------------------------------------------------------------
    # WebSocket handling
    # ---------------------------------------------------------------------
    def register_socketio(self):
        @self.socketio.on(f"{self.base_event}_subscribe_live_feed")
        async def _subscribe_handler(sid):
            await self.handle_subscribe_live_feed(sid)

    async def handle_subscribe_live_feed(self, sid):
        logger.debug(
            f"[{self.base_event}] ******* Client subscribed to live feed: {sid}"
        )
        self._initializing_clients.add(sid)
        all_msgs = self.model.get_all()
        sorted_msgs = sorted(all_msgs.values(), key=lambda v: v.get_id())
        logger.debug(
            f"[{self.base_event}] Sending initial "
            f"state to {self.base_event}, {len(sorted_msgs)} items."
        )
        await self.socketio.enter_room(sid, self.room)
        await self.socketio.emit(
            f"{self.base_event}_initial_state",
            [v.to_dict() for v in sorted_msgs],
            room=self.room,
        )
        self._initializing_clients.discard(sid)

    @publish_from_arg_sync(status=DataFlowStatus.FORWARDED)
    def publish(self, msg: T):
        logger.debug(f"[{self.base_event}] Publishing message: {msg}")
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
                    f"{self.base_event}_{self.t_cls.__name__.lower()}",
                    buffer_copy,
                    room=self.room,
                )

    # ---------------------------------------------------------------------
    # HTTP endpoints via APIRouter
    # ---------------------------------------------------------------------
    def _register_generic_routes(self, u_cls: Optional[Type[U]]):
        if u_cls is None:
            return

        endpoint_name = f"{self.base_event}/{u_cls.__name__.lower()}"
        route_path = f"/{endpoint_name}"

        # Define the handler function within a closure to capture u_cls in order to generate API
        # with the correct object type.
        def make_handler(model_cls):
            @publish_route_async(DataFlowStatus.USER_ACTION, source=endpoint_name)
            async def _incoming_handler(body: model_cls, request: Request):  # type: ignore
                # Extract JWT token from Authorization header
                logger.debug(f"Handling incoming request for endpoint: {endpoint_name}")
                token = request.cookies.get("jwt")
                logger.debug(f"Received request with token: {token}")
                user_info = verify_jwt(token) if token else None
                username = user_info["username"] if user_info else None
                logger.debug(f"Verified username from token: {username}")
                if not SecurityService.get_instance_or_none().is_allowed(
                    username, endpoint_name
                ):
                    logger.debug(
                        f"Unauthorized access attempt by user: {username}"
                        f"to endpoint: {endpoint_name}"
                    )
                    # Forbidden
                    return make_response(
                        status="error",
                        reason="User not authorized for this endpoint.",
                        status_code=403,
                        user=username,
                        endpoint=endpoint_name,
                    )
                logger.debug(
                    f"User {username} is authorized for endpoint: {endpoint_name}"
                )
                logger.debug(f"Request: {request}")
                logger.debug(
                    f"Incoming data for user {username} on endpoint {endpoint_name}: {body}"
                )
                result = self.validate_request_data(body)
                logger.debug(
                    f"Validation result for user {username} on endpoint {endpoint_name}: {result}"
                )
                # Validation error — use the precise message
                if isinstance(result, StatusDTO):
                    return make_response(
                        status="error",
                        reason=result.reason or "Invalid request data",
                        status_code=400,
                        user=username,
                        endpoint=endpoint_name,
                    )

                if self.service:
                    await self.service.handle_controller_message(result)

                # OK
                return make_response(
                    status="ok",
                    reason="Request accepted.",
                    status_code=200,
                    user=username,
                    endpoint=endpoint_name,
                )

            return _incoming_handler

        handler = make_handler(u_cls)
        self.router.post(
            route_path,
            name=endpoint_name,
            tags=[self.base_event],
            operation_id=f"{u_cls.__name__.lower()}",
        )(handler)

    # ---------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------
    @abstractmethod
    def validate_request_data(self, data: U) -> Union[U, StatusDTO]:
        """Return validated data or StatusDTO for errors."""
        pass
