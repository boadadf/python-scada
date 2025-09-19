import asyncio
from flask import Flask
from flask_socketio import SocketIO
from openscada_lite.frontend.datapoints.model import DatapointModel
from openscada_lite.frontend.datapoints.service import DatapointService
from openscada_lite.frontend.datapoints.controller import DatapointController
from openscada_lite.frontend.communications.model import CommunicationsModel
from openscada_lite.frontend.communications.service import CommunicationsService
from openscada_lite.frontend.communications.controller import CommunicationsController
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.backend.communications.connector_manager import ConnectorManager
from openscada_lite.common.config.config import Config

app = Flask(
    __name__,
    static_folder="frontend",  # <-- adjust this path as needed
    static_url_path="/static"
)
socketio = SocketIO(app, cors_allowed_origins="*")
event_bus = EventBus()

#TODO: Dependency Injection?
#TODO: Is there way to initialize all this like using interfaces?
#TODO: Is there a spring framework for Python?
datapointModel = DatapointModel()
datapointController = DatapointController(datapointModel,socketio)
service = DatapointService(event_bus, datapointModel, datapointController)


communicationModel = CommunicationsModel()
communicationController = CommunicationsController(communicationModel,socketio)
communicationService = CommunicationsService(event_bus, communicationModel, communicationController)


connector_manager = ConnectorManager(event_bus)
asyncio.run(connector_manager.init_drivers())

def main():
    print("OpenSCADA-Lite is starting...")
    socketio.run(app, debug=True)

if __name__ == "__main__":
    main()