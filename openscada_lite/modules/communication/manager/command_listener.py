from typing import Protocol
from openscada_lite.common.models.dtos import SendCommandMsg

class CommandListener(Protocol):
    async def on_driver_command(self, msg: SendCommandMsg):
        ...