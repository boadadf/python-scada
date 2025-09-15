from flask import Flask
from flask_socketio import SocketIO
from app.frontend.tags.model import DatapointModel
from app.frontend.tags.service import DatapointService
from app.frontend.tags.controller import DatapointController
from app.common.bus.event_bus import EventBus

app = Flask(
    __name__,
    static_folder="app/frontend",  # <-- adjust this path as needed
    static_url_path="/static"
)
socketio = SocketIO(app, cors_allowed_origins="*")
event_bus = EventBus()

model = DatapointModel()
controller = DatapointController(model,socketio)
service = DatapointService(event_bus, model, controller)
controller.service = service  

controller.register_socketio(socketio)
service._controller = controller

if __name__ == "__main__":
    socketio.run(app, debug=True)