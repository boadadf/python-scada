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
import datetime
from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

scada_router = APIRouter(prefix="/scada")

WEB_DIR = Path(__file__).parent
DIST_DIR = WEB_DIR / "static" / "frontend" / "dist"
INDEX_FILE = DIST_DIR / "index.html"


@scada_router.get("/", response_class=FileResponse)
async def scada_index():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return FileResponse(status_code=404)


# -------------------------
# SCADA Ping Endpoint
# -------------------------
@scada_router.get("/ping")
async def scada_ping():
    return {"status": "ok", "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
