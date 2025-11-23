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
# openscada_lite/web/security_editor/routes.py
import os
import json
import anyio
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Paths
current_dir = Path(__file__).parent
static_dir = current_dir / "static" / "frontend" / "dist"
config_file = Path(__file__).parent.parent.parent / ".." / "config" / "security_config.json"

# API router
security_router = APIRouter(prefix="/security-editor", tags=["SecurityEditor"])

# Mount static frontend files
security_router.mount("/static", StaticFiles(directory=static_dir), name="security_static")


# Serve main React index.html for the editor
@security_router.get("/", response_class=FileResponse)
async def editor_index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return FileResponse(status_code=404)


# -------------------- API Endpoints --------------------


@security_router.get("/api/config", response_class=JSONResponse)
async def get_security_config():
    async with await anyio.open_file(config_file, "r") as file:
        data = await file.read()
        return json.loads(data)

@security_router.post("/api/config", response_class=JSONResponse)
async def save_security_config(request: Request):
    config = await request.json()
    async with await anyio.open_file(config_file, "w") as file:
        await file.write(json.dumps(config, indent=2))
    return {"status": "ok"}


@security_router.post("/api/restart", response_class=JSONResponse)
async def restart_app():
    import sys
    import threading

    def do_restart():
        print("[RESTART] Restarting OpenSCADA-Lite process...")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        os.chdir(project_root)
        python = sys.executable
        os.execl(python, python, "-m", "openscada_lite.app", *sys.argv[1:])

    threading.Thread(target=do_restart).start()
    return {"message": "Restarting OpenSCADA-Lite..."}
