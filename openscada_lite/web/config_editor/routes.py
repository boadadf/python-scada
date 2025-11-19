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
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "config", "system_config.json"
)

config_router = APIRouter(prefix="/config-editor/api", tags=["ConfigEditor"])

@config_router.get("/config", response_class=JSONResponse)
async def get_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

@config_router.post("/config", response_class=JSONResponse)
async def save_config(request: Request):
    config = await request.json()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    return {"status": "ok"}


@config_router.post("/restart", response_class=JSONResponse)
async def restart_app():
    import sys, os, threading
    def do_restart():
        print("[RESTART] Restarting OpenSCADA-Lite process...")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        os.chdir(project_root)
        python = sys.executable
        os.execl(python, python, "-m", "openscada_lite.app", *sys.argv[1:])
    threading.Thread(target=do_restart).start()
    return {"message": "Restarting OpenSCADA-Lite..."}
