from typing import Protocol, runtime_checkable
from openscada_lite.modules.communication.drivers.driver_protocol import DriverProtocol
from openscada_lite.common.models.dtos import TagUpdateMsg

@runtime_checkable
class ServerProtocol(DriverProtocol, Protocol):
    async def handle_tag_update(self, msg: TagUpdateMsg) -> None: ...
    def set_command_listener(self, listener) -> None: ...