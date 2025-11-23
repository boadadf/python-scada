# -----------------------------------------------------------------------------
# Static & Frontend Mounts
# -----------------------------------------------------------------------------
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path


def mount_enpoints(app):
    web_dir = Path(__file__).parent

    # SCADA: serve the build folder directly
    app.mount(
        "/scada",
        StaticFiles(directory=web_dir / "scada" / "static" / "frontend" / "dist", html=True),
        name="scada",
    )

    # Config Editor
    app.mount(
        "/config-editor",
        StaticFiles(
            directory=web_dir / "config_editor" / "static" / "frontend" / "dist",
            html=True,
        ),
        name="config_editor",
    )

    # Security Editor
    app.mount(
        "/security-editor",
        StaticFiles(
            directory=web_dir / "security_editor" / "static" / "frontend" / "dist", html=True
        ),
        name="security_editor",
    )

    # Path to icons directory (relative to this file)
    icons_path = web_dir / "icons"

    app.mount("/static/icons", StaticFiles(directory=icons_path), name="icons")

    # Redirect root to SCADA
    @app.get("/")
    async def index():
        return RedirectResponse("/scada")
