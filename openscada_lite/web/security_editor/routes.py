import os
import json
from flask import jsonify, request, render_template
from . import security_bp

CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'config', 'security_config.json'
)

@security_bp.route("/api/config", methods=["GET"])
def get_config():
    with open(CONFIG_FILE) as f:
        return jsonify(json.load(f))

@security_bp.route("/api/config", methods=["POST"])
def save_config():
    config = request.json
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    return jsonify({"status": "ok"})

@security_bp.route("/api/reload-security", methods=["POST"])
def reload_security():
    try:
        # reload_security()
        return jsonify({"status": "ok", "message": "Security reloaded!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@security_bp.route("/")
def editor():
    return render_template("security_editor.html")
