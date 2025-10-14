import importlib
import os
import sys
import asyncio
from flask import Flask, send_from_directory
from flask_socketio import SocketIO



# Set SCADA_CONFIG_PATH from command-line argument or default
if "SCADA_CONFIG_PATH" not in os.environ:
    if len(sys.argv) > 1:
        os.environ["SCADA_CONFIG_PATH"] = sys.argv[1]
    else:
        # Default to ./config/system_config.json
        os.environ["SCADA_CONFIG_PATH"] = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "config", "system_config.json")
        )
print(f"[APP] Using SCADA_CONFIG_PATH: {os.environ['SCADA_CONFIG_PATH']}")

from openscada_lite.modules.security.controller import SecurityController
from openscada_lite.modules.security.model import SecurityModel
from openscada_lite.modules.security.service import SecurityService
from openscada_lite.common.config.config import Config
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.web.config_editor.routes import config_bp
from openscada_lite.web.security_editor.routes import security_bp
from openscada_lite.web.scada.routes import scada_bp

# ---------------------------------------------------------------------
# Flask & SocketIO setup
# ---------------------------------------------------------------------
app = Flask(
    __name__,
    static_folder="web",
    static_url_path="/static"
)

# Register security blueprint
app.register_blueprint(scada_bp)

# Register config editor blueprint
app.register_blueprint(config_bp)

# Register security editor blueprint
app.register_blueprint(security_bp)

@app.route('/svg/<path:filename>')
def serve_svg(filename):
    svg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'svg'))
    return send_from_directory(svg_dir, filename)

socketio = SocketIO(app, cors_allowed_origins="*")
event_bus = EventBus.get_instance()

system_config = Config.get_instance().load_system_config()

# If you need animation config:
# animation_config = Config.get_instance().get_animation_config()


# ---------------------------------------------------------------------
# Module initialization
# ---------------------------------------------------------------------
def initialize_modules(config: dict, socketio: SocketIO, event_bus: EventBus) -> dict:
    """Dynamically load and initialize all configured modules."""
    module_instances = {}

    for module_entry in config.get("modules", []):
        if isinstance(module_entry, dict):
            module_name = module_entry.get("name", "")
            module_config = module_entry.get("config", {})
        else:
            module_name = str(module_entry)
            module_config = {}

        base_path = f"openscada_lite.modules.{module_name}"
        class_prefix = module_name.capitalize()

        print(f"[INIT] Loading module: {module_name}")

        # Import classes dynamically
        model_cls = getattr(importlib.import_module(f"{base_path}.model"), f"{class_prefix}Model")
        controller_cls = getattr(importlib.import_module(f"{base_path}.controller"), f"{class_prefix}Controller")
        service_cls = getattr(importlib.import_module(f"{base_path}.service"), f"{class_prefix}Service")

        print(f"Instantiating: {module_name}")
        # Instantiate
        model = model_cls()
        print(f"Model: {model}")
        controller = controller_cls(model, socketio, module_name, app)
        print(f"Controller: {controller}")
        service = service_cls(event_bus, model, controller)
        print(f"Service: {service}")
        
        module_instances[module_name] = {
            "model": model,
            "controller": controller,
            "service": service,
            "config": module_config,
        }

    return module_instances


module_instances = initialize_modules(system_config, socketio, event_bus)

async def async_init_all(module_instances):
    for mod in module_instances.values():
        service = mod.get("service")
        if hasattr(service, "async_init"):
            await service.async_init()

asyncio.run(async_init_all(module_instances))

#Security modules are not part of the dynamic modules
print(f"[APP] Initializing Security Module {(app)}")
security_model = SecurityModel(app)
security_service = SecurityService(event_bus, security_model)
security_controller = SecurityController(security_model, security_service)
security_controller.register_routes(app)


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
def main():
    print("✅ OpenSCADA-Lite is starting...")
    socketio.run(app, debug=True)


if __name__ == "__main__":
    main()
