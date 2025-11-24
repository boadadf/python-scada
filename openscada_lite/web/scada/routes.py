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
from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

scada_router = APIRouter(prefix="/scada")

WEB_DIR = Path(__file__).parent
DIST_INDEX = WEB_DIR / "static" / "frontend" / "dist" / "index.html"


@scada_router.get("/")
@scada_router.get("/login")
async def scada_index():
    if DIST_INDEX.exists():
        return FileResponse(DIST_INDEX)
    return {"error": "scada index.html not found"}
