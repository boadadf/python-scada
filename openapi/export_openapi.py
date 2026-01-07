# export_openapi.py
import asyncio
import json
from pathlib import Path
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

# Ensure src/ is in path
import sys

SRC_ROOT = Path(__file__).parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from openscada_lite.modules.registry import MODULES
from openscada_lite.modules.loader import module_loader
from openscada_lite.modules.base.base_controller import BaseController
from openscada_lite.common.bus.event_bus import EventBus  # real EventBus

from openscada_lite.web.config_editor.routes import config_router
from openscada_lite.web.security_editor.routes import security_router
from openscada_lite.web.scada.routes import scada_router
from openscada_lite.web.mounter import mount_enpoints


# --- Minimal dummy SocketIO just to allow controller registration ---
class DummySocketIO:
    def on(self, *args, **kwargs):
        return lambda f: f

    def emit(self, *args, **kwargs):
        pass


# --- Fake config generated from registry ---
fake_config = {"modules": [{"name": name} for name in MODULES]}


def create_api_app() -> FastAPI:
    app = FastAPI(title="OpenSCADA-Lite", version="0.0.1", debug=False)

    # Static routers
    app.include_router(config_router)
    app.include_router(security_router)
    app.include_router(scada_router)
    mount_enpoints(app)

    # Use real EventBus singleton
    event_bus = EventBus.get_instance()

    # Load modules exactly like the real app
    asyncio.run(
        module_loader(
            config=fake_config,
            socketio_obj=DummySocketIO(),
            event_bus=event_bus,
            app=app,
        )
    )

    return app


def export_openapi():
    app = create_api_app()
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    output_path = Path(__file__).parent / "openapi.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)

    print(f"[OpenAPI] Schema exported to {output_path}")


if __name__ == "__main__":
    export_openapi()
