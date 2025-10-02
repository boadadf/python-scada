from flask import Blueprint

config_bp = Blueprint(
    "config_bp",
    __name__,
    static_folder="static",
    static_url_path="/config-editor/static",   # ensures correct static path
    template_folder="templates",
    url_prefix="/config-editor"
)

# Import routes so they attach to this blueprint
from . import routes