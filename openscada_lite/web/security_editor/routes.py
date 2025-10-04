import os
import json
from flask import jsonify, request, render_template
from . import security_bp

CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'config', 'security_config.json'
)

@security_bp.route("/")
def editor():
    return render_template("security_editor.html")
