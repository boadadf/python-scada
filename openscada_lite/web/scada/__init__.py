from flask import Blueprint

scada_bp = Blueprint(
    "scada_bp",
    __name__,
    static_folder="static",
    static_url_path="/scada/static",   # ensures correct static path
    template_folder="templates",
    url_prefix="/scada"
)

# Import routes so they attach to this blueprint
from . import routes