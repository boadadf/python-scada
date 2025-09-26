import importlib
import json
import os
import sys
import asyncio
from flask import Flask
from flask_socketio import SocketIO

from openscada_lite.core.rule.rule_manager import RuleEngine
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.core.communications.connector_manager import ConnectorManager


# ---------------------------------------------------------------------
# Flask & SocketIO setup
# ---------------------------------------------------------------------
app = Flask(
    __name__,
    static_folder="web",     # <-- adjust this path as needed
    static_url_path="/static"
)
socketio = SocketIO(app, cors_allowed_origins="*")
event_bus = EventBus.get_instance()


# ---------------------------------------------------------------------
# Configuration loader
# ---------------------------------------------------------------------
def load_config(config_path: str) -> dict:
    """Load JSON config file."""
    with open(config_path) as f:
        return json.load(f)


def resolve_config_path() -> str:
    """
    Resolve config path by priority:
    1. Environment variable SCADA_CONFIG_FILE
    2. Command-line argument
    3. Default config.json in project root
    """
    return (
        os.environ.get("SCADA_CONFIG_FILE")
        or (sys.argv[1] if len(sys.argv) > 1 else None)
        or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))
    )


config = load_config(resolve_config_path())


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
        controller = controller_cls(model, socketio, module_name)
        service = service_cls(event_bus, model, controller)

        module_instances[module_name] = {
            "model": model,
            "controller": controller,
            "service": service,
            "config": module_config,
        }

    return module_instances


module_instances = initialize_modules(config, socketio, event_bus)


# ---------------------------------------------------------------------
# Rule engine & connector manager
# ---------------------------------------------------------------------
RuleEngine.get_instance(event_bus)

connector_manager = ConnectorManager(event_bus)
# Run async initialization safely at startup
asyncio.run(connector_manager.init_drivers())


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
def main():
    print("✅ OpenSCADA-Lite is starting...")
    socketio.run(app, debug=True)


if __name__ == "__main__":
    main()
