import asyncio
import json
import os
from openscada_lite.common.config.config import Config
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import DataFlowEventMsg, StatusDTO
from openscada_lite.common.bus.event_types import EventType


class TrackingService(BaseService[DataFlowEventMsg, StatusDTO, DataFlowEventMsg]):
    def __init__(self, event_bus, model, controller):
        super().__init__(event_bus, model, controller, DataFlowEventMsg, StatusDTO, DataFlowEventMsg)
        self.config = Config.get_instance().get_module_config("tracking")
        self.file_path = self.config.get("file_path", "flow_events.log")
        self.tailing_task = None

        if self.config.get("mode") == "bus":
            self.event_bus.subscribe(EventType.FLOW_EVENT, self.handle_bus_message)

    async def start(self, from_start: bool = False):
        """Start background file tailing if file mode is active."""
        if self.config.get("mode") == "file":
            # Ensure the file exists
            open(self.file_path, "a").close()
            self.tailing_task = asyncio.create_task(self.tail_file(self.file_path, from_start=from_start))

    def should_accept_update(self, msg: DataFlowEventMsg) -> bool:
        return True

    async def tail_file(self, file_path: str, from_start: bool = False):
        """Continuously read new lines from the file and process them as DataFlowEventMsg."""
        while not os.path.exists(file_path):
            print(f"[TRACKING] Waiting for file {file_path} to be created...")
            await asyncio.sleep(0.5)
        print(f"[TRACKING] Starting to tail file: {file_path}") 
        with open(file_path, "r") as f:
            # Optionally start from the beginning
            print(f"[TRACKING] Tailing file from_start={from_start}")
            if not from_start:
                f.seek(0, os.SEEK_END)
            print(f"[TRACKING] File position after seek: {f.tell()}")
            while True:
                line = f.readline()
                print(f"[TRACKING] Read line: {line.strip()}")
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                await self._process_line(line)

    async def _process_line(self, line: str):
        print(f"[TRACKING] Processing line: {line.strip()}")
        try:
            data = json.loads(line.strip())
            event = DataFlowEventMsg(**data)
            self.model.update(event)
            self.controller.publish(event)
        except Exception as e:
            print(f"[TRACKING ERROR] Failed to parse line: {e} -> {line}")
