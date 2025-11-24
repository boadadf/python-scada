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
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
import socketio
import uvicorn
from fastapi import FastAPI

from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.config.config import Config

from openscada_lite.modules.loader import module_loader

from openscada_lite.web.config_editor.routes import config_router
from openscada_lite.web.security_editor.routes import security_router
from openscada_lite.web.mounter import mount_enpoints

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
    task = asyncio.create_task(module_loader(system_config, sio, event_bus, app))
    await task
    yield
    print("[LIFESPAN] Shutdown complete")


app = FastAPI(title="OpenSCADA-Lite", version="2.0", lifespan=lifespan)
app.include_router(config_router)
app.include_router(security_router)
mount_enpoints(app)

# Single ASGI entrypoint combining Socket.IO + FastAPI
asgi_app = socketio.ASGIApp(sio, other_asgi_app=app)

# -----------------------------------------------------------------------------
# Core Security Module
# -----------------------------------------------------------------------------
event_bus = EventBus.get_instance()
system_config = Config.get_instance().load_system_config()


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
