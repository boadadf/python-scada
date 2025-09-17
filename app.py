import asyncio
from flask import Flask
from flask_socketio import SocketIO
from app.frontend.datapoints.model import DatapointModel
from app.frontend.datapoints.service import DatapointService
from app.frontend.datapoints.controller import DatapointController
from app.frontend.communications.model import CommunicationsModel
from app.frontend.communications.service import CommunicationsService
from app.frontend.communications.controller import CommunicationsController

from app.common.bus.event_bus import EventBus
from app.backend.communications.connector_manager import ConnectorManager
from app.common.config.config import Config

app = Flask(
    __name__,
    static_folder="app/frontend",  # <-- adjust this path as needed
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

if __name__ == "__main__":
    socketio.run(app, debug=True)