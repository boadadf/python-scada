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
# openscada_lite/web/config_editor/routes.py
import os
import json
import anyio
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

SYSTEM_CONFIG_FILENAME = "system_config.json"

CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "config", SYSTEM_CONFIG_FILENAME
)

config_router = APIRouter(prefix="/config-editor/api", tags=["ConfigEditor"])

def normalize_config_filename(name: str) -> str:
    if name == "system_config":
        return SYSTEM_CONFIG_FILENAME
    if name.endswith(SYSTEM_CONFIG_FILENAME):
        return name
    if name.endswith(".json"):
        return name
    return f"{name}_{SYSTEM_CONFIG_FILENAME}"


@config_router.get("/config/{name}", response_class=JSONResponse)
async def get_config_by_name(name: str):
    config_dir = os.path.dirname(CONFIG_FILE)
    filename = normalize_config_filename(name)
    path = os.path.join(config_dir, filename)
    if not os.path.isfile(path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    async with await anyio.open_file(path, "r") as file:
        data = await file.read()
    return json.loads(data)


@config_router.get("/configs", response_class=JSONResponse)
async def list_configs():
    config_dir = os.path.dirname(CONFIG_FILE)
    files = [f for f in os.listdir(config_dir) if f.endswith(f"_{SYSTEM_CONFIG_FILENAME}")]
    # Strip suffix for user display
    display_names = [f.replace(f"_{SYSTEM_CONFIG_FILENAME}", "") for f in files]
    return display_names


@config_router.post("/config", response_class=JSONResponse)
async def save_config(request: Request):
    config = await request.json()
    async with await anyio.open_file(CONFIG_FILE, "w") as file:
        await file.write(json.dumps(config, indent=2))
    return {"status": "ok"}


@config_router.post("/saveas", response_class=JSONResponse)
async def save_config_as(request: Request):
    payload = await request.json()
    config = payload.get("config")
    name = payload.get("filename")
    if not name:
        return JSONResponse({"error": "Invalid filename"}, status_code=400)
    filename = normalize_config_filename(name)
    config_dir = os.path.dirname(CONFIG_FILE)
    path = os.path.join(config_dir, filename)
    async with await anyio.open_file(path, "w") as file:
        await file.write(json.dumps(config, indent=2))
    return {"status": "ok", "filename": filename}


@config_router.post("/restart", response_class=JSONResponse)
async def restart_app():
    async def delayed_exit():
        await anyio.sleep(0.5)  # Let HTTP response complete
        print("[RESTART] Exiting process to trigger Docker restart...")
        os._exit(1)  # Immediately kill the container

    anyio.create_task(delayed_exit())
    return {"message": "Restarting OpenSCADA-Lite container..."}
