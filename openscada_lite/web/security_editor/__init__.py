from flask import Blueprint

security_bp = Blueprint(
    "security_bp",
    __name__,
    static_folder="static",
    static_url_path="/security-editor/static",   # ensures correct static path
    template_folder="templates",
    url_prefix="/security-editor"
)

# Import routes so they attach to this blueprint
from . import routes