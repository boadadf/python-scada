# -----------------------------------------------------------------------------
# Copyright 2025 Daniel&Hector Fernandez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
import os
import sys
import importlib
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.config.config import Config

from openscada_lite.modules.security.model import SecurityModel
from openscada_lite.modules.security.service import SecurityService
from openscada_lite.modules.security.controller import SecurityController

from openscada_lite.web.config_editor.routes import config_router
# -----------------------------------------------------------------------------
# Socket.IO
# -----------------------------------------------------------------------------
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    ping_interval=25,
    ping_timeout=120,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[LIFESPAN] Startup starting...")
    asyncio.create_task(async_init_all())
    yield
    print("[LIFESPAN] Shutdown complete")

app = FastAPI(title="OpenSCADA-Lite", version="2.0", lifespan=lifespan)
app.include_router(config_router)

# Single ASGI entrypoint combining Socket.IO + FastAPI
asgi_app = socketio.ASGIApp(sio, other_asgi_app=app)

# -----------------------------------------------------------------------------
# Static & Frontend Mounts
# -----------------------------------------------------------------------------
web_dir = Path(__file__).parent / "web"

# SCADA: serve the build folder directly
app.mount(
    "/scada",
    StaticFiles(directory=web_dir / "scada" / "static" / "frontend" / "dist", html=True),
    name="scada",
)

# Config Editor
app.mount(
    "/config-editor",
    StaticFiles(
        directory=web_dir / "config_editor" / "static" / "frontend" / "dist",
        html=True,
    ),
    name="config_editor",
)

# Security Editor
app.mount(
    "/security-editor",
    StaticFiles(directory=web_dir / "security_editor" / "static", html=True),
    name="security_editor",
)

# Path to icons directory (relative to this file)
icons_path = os.path.join(os.path.dirname(__file__), "web", "icons")

app.mount("/static/icons", StaticFiles(directory=icons_path), name="icons")

# Optional: serve SVGs
@app.get("/svg/{filename:path}")
async def svg(filename: str):
    svg_dir = Path(__file__).parent.parent / "config" / "svg"
    file = svg_dir / filename
    if file.exists():
        return FileResponse(file)
    return FileResponse(status_code=404)

# Redirect root to SCADA
@app.get("/")
async def index():
    return RedirectResponse("/scada")

# -----------------------------------------------------------------------------
# Core Security Module
# -----------------------------------------------------------------------------
event_bus = EventBus.get_instance()
system_config = Config.get_instance().load_system_config()

security_model = SecurityModel()
security_service = SecurityService(event_bus, security_model)
security_controller = SecurityController(security_model, security_service)
security_controller.register_routes(app)

# -----------------------------------------------------------------------------
# Dynamic Module Loader
# -----------------------------------------------------------------------------
def initialize_modules(config: dict, socketio_obj, event_bus_obj) -> dict:
    module_instances = {}
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

        try:
            controller:BaseController = controller_cls(model, socketio_obj, module_name, app)
        except TypeError:
            controller:BaseController = controller_cls(model, socketio_obj, module_name)
        router = controller.get_router()
        print(f"[INIT] Module router: {router}")
        if router:
            app.include_router(router)

        service = service_cls(event_bus_obj, model, controller)
        if hasattr(controller, "set_service"):
            controller.set_service(service)

        if hasattr(controller, "register_routes"):
            try:
                controller.register_routes(app)
            except Exception as e:
                print(f"[INIT] Warning: register_routes failed for {module_name}: {e}")

        module_instances[module_name] = {
            "model": model,
            "controller": controller,
            "service": service,
        }

    return module_instances

module_instances = initialize_modules(system_config, sio, event_bus)

# -----------------------------------------------------------------------------
# Async module init
# -----------------------------------------------------------------------------
async def async_init_all():
    for name, mod in module_instances.items():
        service = mod["service"]
        if hasattr(service, "async_init"):
            print(f"[INIT] async_init: {name}")
            await service.async_init()

# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if "SCADA_CONFIG_PATH" not in os.environ:
        cfg = next((arg for arg in args if not arg.startswith("-")), None)
        if cfg and Path(cfg).exists():
            os.environ["SCADA_CONFIG_PATH"] = str(Path(cfg).resolve())
        else:
            os.environ["SCADA_CONFIG_PATH"] = str(
                Path(__file__).parent.parent / "config" / "system_config.json"
            )

    print(f"[APP] SCADA_CONFIG_PATH = {os.environ['SCADA_CONFIG_PATH']}")
    print("[APP] Starting OpenSCADA-Lite (FastAPI / ASGI / Socket.IO)")

    uvicorn.run(
        "openscada_lite.app:asgi_app",
        host="0.0.0.0",
        port=5443,
        reload=True,
        ws_max_size=16 * 1024 * 1024,
    )


if __name__ == "__main__":
    main()