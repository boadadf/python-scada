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
from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Paths
current_dir = Path(__file__).parent
static_dir = current_dir / "static" / "frontend" / "dist"
config_file = Path(__file__).parent.parent.parent / ".." / "config" / "security_config.json"

# API router
security_router = APIRouter(
    prefix="/security-editor", tags=["SecurityEditor"], include_in_schema=False
)

# Mount static frontend files
security_router.mount("/static", StaticFiles(directory=static_dir), name="security_static")


# Serve main React index.html for the editor
@security_router.get("/", response_class=FileResponse)
async def editor_index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return FileResponse(status_code=404)
