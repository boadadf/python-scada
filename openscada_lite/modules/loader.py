# -----------------------------------------------------------------------------
# Dynamic Module Loader
# -----------------------------------------------------------------------------
import importlib
from openscada_lite.modules.security.controller import SecurityController
from openscada_lite.modules.security.model import SecurityModel
from openscada_lite.modules.security.service import SecurityService
from openscada_lite.modules.base.base_controller import BaseController

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
        controller_cls = getattr(importlib.import_module(f"{base_path}.controller"), f"{class_prefix}Controller")
        service_cls = getattr(importlib.import_module(f"{base_path}.service"), f"{class_prefix}Service")

        model = model_cls()
        controller:BaseController = controller_cls(model, socketio_obj, module_name, app)
        service = service_cls(event_bus, model, controller)
        controller.set_service(service)
        if hasattr(service, "async_init"):
            print(f"[INIT] async_init: {module_name}")
            await service.async_init()

    print("[INIT] Loading Security module")
    #Security module is always loaded regardless of config
    security_model = SecurityModel()
    security_controller = SecurityController(security_model, socketio_obj, "security", app)
    security_service = SecurityService(event_bus, security_model, security_controller)    
    security_controller.set_service(security_service)
    print(f"[INIT] Security module loaded")