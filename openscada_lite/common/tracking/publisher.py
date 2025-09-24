import datetime
import json
from openscada_lite.common.tracking.utils import safe_serialize
from openscada_lite.common.bus.event_bus import EventBus, EventType
from openscada_lite.common.config.config import Config
from openscada_lite.common.models.dtos import DTO, DataFlowEventMsg
from openscada_lite.common.tracking.tracking_types import DataFlowStatus


class TrackingPublisher:
    def __init__(self):
        config = Config.get_instance()
        tracking_cfg = config.get_module_config("tracking")
        self.enabled = bool(tracking_cfg)
        self.mode = tracking_cfg.get("mode", "none")
        self.file_path = tracking_cfg.get("file_path", "flow_events.log")

    async def publish_data_flow_event(self, dto: DTO, source: str, status: DataFlowStatus):
        if not self.enabled:
            return
        flow_event = DataFlowEventMsg(
            track_id=dto.track_id,
            event_type=dto.__class__.__name__,
            source=source,
            status=status,
            timestamp=datetime.datetime.now(),
            payload=dto.get_track_payload()
        )
        if self.mode == "file":
            # Do file I/O asynchronously if you want (aiofiles), but for now blocking is fine
            with open(self.file_path, "a") as f:
                f.write(json.dumps(flow_event.get_track_payload(), default=safe_serialize) + "\n")
        elif self.mode == "bus":
            EventBus.get_instance().publish(EventType.FLOW_EVENT, flow_event)
