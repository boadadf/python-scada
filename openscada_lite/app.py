import asyncio
from flask import Flask
from flask_socketio import SocketIO
from openscada_lite.modules.datapoints.model import DatapointModel
from openscada_lite.modules.datapoints.service import DatapointService
from openscada_lite.modules.datapoints.controller import DatapointController
from openscada_lite.modules.communications.model import CommunicationsModel
from openscada_lite.modules.communications.service import CommunicationsService
from openscada_lite.modules.communications.controller import CommunicationsController
from openscada_lite.modules.commands.model import CommandModel
from openscada_lite.modules.commands.service import CommandService
from openscada_lite.modules.commands.controller import CommandController
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.backend.communications.connector_manager import ConnectorManager

app = Flask(
    __name__,
    static_folder="web",  # <-- adjust this path as needed
    static_url_path="/static"
)
socketio = SocketIO(app, cors_allowed_origins="*")
event_bus = EventBus()

#TODO: Is there way to initialize all this like using interfaces?
#TODO: Is there a spring framework for Python?
datapointModel = DatapointModel()
datapointController = DatapointController(datapointModel,socketio)
service = DatapointService(event_bus, datapointModel, datapointController)

communicationModel = CommunicationsModel()
communicationController = CommunicationsController(communicationModel,socketio)
communicationService = CommunicationsService(event_bus, communicationModel, communicationController)

commandModel = CommandModel()
commandController = CommandController(commandModel,socketio)
commandService = CommandService(event_bus, commandModel, commandController)

connector_manager = ConnectorManager(event_bus)
asyncio.run(connector_manager.init_drivers())

def main():
    print("OpenSCADA-Lite is starting...")
    socketio.run(app, debug=True)

if __name__ == "__main__":
    main()