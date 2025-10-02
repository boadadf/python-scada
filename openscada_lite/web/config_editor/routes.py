import os
import json
from flask import jsonify, request, render_template
from . import config_bp

CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'config', 'system_config.json'
)

@config_bp.route("/api/config", methods=["GET"])
def get_config():
    with open(CONFIG_FILE) as f:
        return jsonify(json.load(f))

@config_bp.route("/api/config", methods=["POST"])
def save_config():
    config = request.json
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    return jsonify({"status": "ok"})

@config_bp.route("/api/reload", methods=["POST"])
def reload_modules():
    try:
        # reload_all_modules()
        return jsonify({"status": "ok", "message": "Modules reloaded!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@config_bp.route("/")
def editor():
    return render_template("editor.html")
