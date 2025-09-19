from openscada_lite.common.bus.event_types import EventType
from openscada_lite.frontend.communications.model import CommunicationsModel
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.frontend.communications.controller import CommunicationsController

class CommunicationsService:
    def __init__(self, event_bus: EventBus, model: CommunicationsModel, controller: CommunicationsController):
        self.event_bus = event_bus
        self.model = model
        self.controller = controller
        if controller:
            controller.service = self
        self.event_bus.subscribe(EventType.DRIVER_CONNECT_STATUS, self.on_driver_connect_status)

    async def on_driver_connect_status(self, data):
        print(f"Driver status update received: {data}")
        if isinstance(data, dict):
            server_name = data.get("server_name") or data.get("driver_name")
            status = data.get("status")
        else:
            server_name = getattr(data, "server_name", None) or getattr(data, "driver_name", None)
            status = getattr(data, "status", None)
        self.model.set_status(server_name, status)
        self.controller.publish_status(server_name, status)

    async def send_connect_status(self, server_name, status):
        await self.event_bus.publish(EventType.DRIVER_CONNECT, {"server_name": server_name, "status": status})
