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
# -----------------------------------------------------------------------------
# Copyright 2025 Daniel&Hector Fernandez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# -----------------------------------------------------------------------------
import os
import sys
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
import socketio
from fastapi import FastAPI
import logging
import logging.config
import json

from fastapi.openapi.utils import get_openapi

from openscada_lite.common.tracking.publisher import TrackingPublisher
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.config.config import Config
from openscada_lite.modules.loader import module_loader
from openscada_lite.web.config_editor.routes import config_router
from openscada_lite.web.security_editor.routes import security_router
from openscada_lite.web.scada.routes import scada_router
from openscada_lite.web.mounter import mount_enpoints


# -----------------------------------------------------------------------------
# Generate OpenAPI schema
# -----------------------------------------------------------------------------
def export_openapi_schema(app: FastAPI, output_path: Path):
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
def get_logging_config_path(args=None):
    env_var = "LOGGING_CONFIG_PATH"
    if env_var in os.environ:
        return os.environ[env_var]
    cfg = next((arg for arg in (args or []) if arg.startswith("--logging-config=")), None)
    if cfg:
        return cfg.split("=", 1)[1]
    return str(Path(__file__).parent.parent.parent / "config" / "logging_config.json")


logging_config_path = get_logging_config_path(sys.argv[1:])
with open(logging_config_path, "r") as f:
    config = json.load(f)
logging.config.dictConfig(config)

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Socket.IO server
# -----------------------------------------------------------------------------
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    ping_interval=25,
    ping_timeout=120,
)

# -----------------------------------------------------------------------------
# Core singletons
# -----------------------------------------------------------------------------
event_bus = EventBus.get_instance()
# Resolve configuration directory (env > CLI > default) early
def get_config_dir(args=None):
    env_var = "SCADA_CONFIG_PATH"
    if env_var in os.environ and os.environ[env_var]:
        return os.environ[env_var]
    cfg = next((arg for arg in (args or []) if arg.startswith("--config-dir=")), None)
    if cfg:
        return cfg.split("=", 1)[1]
    # Default to packaged config directory
    return str(Path(__file__).parent.parent / "config")

CONFIG_DIR = get_config_dir(sys.argv[1:])
# Ensure downstream utilities relying on env see the same path
os.environ["SCADA_CONFIG_PATH"] = CONFIG_DIR

system_config = Config.get_instance(CONFIG_DIR).load_system_config()
publisher = TrackingPublisher.get_instance()


# -----------------------------------------------------------------------------
# Lifespan for FastAPI
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[LIFESPAN] Startup starting...")

    # Config path is already set before app init; keep as-is

    loop = asyncio.get_running_loop()
    publisher.initialize(loop)

    try:
        await module_loader(system_config, sio, event_bus, app)
    except Exception as e:
        logger.exception("[LIFESPAN] Error loading modules: %s", e)
    publisher.enable()
    logger.info("[LIFESPAN] Startup complete")
    yield

    # Shutdown publisher gracefully
    publisher.shutdown()
    logger.info("[LIFESPAN] Shutdown complete")


# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(title="OpenSCADA-Lite", version="0.0.1", lifespan=lifespan, debug=True)
app.include_router(config_router)
app.include_router(security_router)
app.include_router(scada_router)
mount_enpoints(app)

# ASGI combining Socket.IO + FastAPI
asgi_app = socketio.ASGIApp(sio, other_asgi_app=app)
