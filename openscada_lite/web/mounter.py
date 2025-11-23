from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path


def mount_enpoints(app):
    web_dir = Path(__file__).parent

    def safe_mount(path: str, directory: Path, name: str):
        if directory.exists():
            app.mount(path, StaticFiles(directory=directory, html=True), name=name)
        else:
            # Prevent application crash in environments without frontend build artifacts
            print(f"⚠ Skipping mount '{name}': {directory} not found")

    # SCADA
    safe_mount(
        "/scada",
        web_dir / "scada" / "static" / "frontend" / "dist",
        "scada",
    )

    # Config Editor
    safe_mount(
        "/config-editor",
        web_dir / "config_editor" / "static" / "frontend" / "dist",
        "config_editor",
    )

    # Security Editor
    safe_mount(
        "/security-editor",
        web_dir / "security_editor" / "static" / "frontend" / "dist",
        "security_editor",
    )

    # Icons directory (this usually exists; still safe to check)
    safe_mount(
        "/static/icons",
        web_dir / "icons",
        "icons",
    )

    # Root redirect
    @app.get("/")
    async def index():
        return RedirectResponse("/scada")
