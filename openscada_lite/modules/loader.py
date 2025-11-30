# -----------------------------------------------------------------------------
# Dynamic Module Loader
# -----------------------------------------------------------------------------
import importlib
from openscada_lite.modules.security.controller import SecurityController
from openscada_lite.modules.security.model import SecurityModel
from openscada_lite.modules.security.service import SecurityService
from openscada_lite.modules.base.base_controller import BaseController
import logging

logger = logging.getLogger(__name__)


async def module_loader(config: dict, socketio_obj, event_bus, app) -> dict:
    for module_entry in config.get("modules", []):
        if isinstance(module_entry, dict):
            module_name = module_entry.get("name", "")
        else:
            module_name = str(module_entry)

        base_path = f"openscada_lite.modules.{module_name}"
        class_prefix = module_name.capitalize()

        print(f"[INIT] Loading module: {module_name}")

        model_cls = getattr(importlib.import_module(f"{base_path}.model"), f"{class_prefix}Model")
        print(f"[INIT] Model class loaded: {module_name}")
        controller_cls = getattr(
            importlib.import_module(f"{base_path}.controller"), f"{class_prefix}Controller"
        )
        print(f"[INIT] Controller class loaded: {module_name}")
        service_cls = getattr(
            importlib.import_module(f"{base_path}.service"), f"{class_prefix}Service"
        )
        print(f"[INIT] Service class loaded: {module_name}")

        model = model_cls()
        print(f"[INIT] Model initialized: {module_name}")
        controller: BaseController = controller_cls(model, socketio_obj, module_name, app)
        print(f"[INIT] Controller initialized: {module_name}")
        service = service_cls(event_bus, model, controller)
        print(f"[INIT] Service initialized: {module_name}")
        controller.set_service(service)
        if hasattr(service, "async_init"):
            print(f"[INIT] async_init: {module_name}")
            await service.async_init()

    print("[INIT] Loading Security module")
    # Security module is always loaded regardless of config
    security_model = SecurityModel()
    security_controller = SecurityController(security_model, socketio_obj, "security", app)
    security_service = SecurityService(event_bus, security_model, security_controller)
    security_controller.set_service(security_service)
    print("[INIT] Security module loaded")
