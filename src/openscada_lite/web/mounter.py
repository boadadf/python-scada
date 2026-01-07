# -----------------------------------------------------------------------------
# Static & Frontend Mounts
# -----------------------------------------------------------------------------
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def mount_enpoints(app):
    web_dir = Path(__file__).parent

    def safe_mount(path: str, directory: Path, name: str):
        if directory.exists():
            app.mount(path, StaticFiles(directory=directory, html=True), name=name)
            logger.debug(f"Mounted '{name}' at '{path}'")
        else:
            logger.warning(f"Skipping mount '{name}': {directory} does not exist")

    # -------------------------
    # SCADA SPA
    # -------------------------
    safe_mount(
        "/scada",
        web_dir / "scada" / "static" / "frontend" / "dist",
        "scada",
    )

    # -------------------------
    # Config Editor
    # -------------------------
    safe_mount(
        "/config-editor",
        web_dir / "config_editor" / "static" / "frontend" / "dist",
        "config_editor",
    )

    # -------------------------
    # Security Editor
    # -------------------------
    safe_mount(
        "/security-editor",
        web_dir / "security_editor" / "static" / "frontend" / "dist",
        "security_editor",
    )

    # -------------------------
    # Icons
    # -------------------------
    safe_mount(
        "/static/icons",
        web_dir / "icons",
        "icons",
    )

    # -------------------------
    # Config SVGs
    # -------------------------
    safe_mount(
        "/config/svg",
        web_dir.parent.parent / "config" / "svg",
        "config_svg",
    )

    # -------------------------
    # Root redirect to SCADA
    # -------------------------
    @app.get("/")
    async def index():
        return RedirectResponse("/scada")
