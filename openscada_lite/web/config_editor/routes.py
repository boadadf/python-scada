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

import os
import json
import sys
import threading
from flask import jsonify, request, render_template
from . import config_bp

CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "config", "system_config.json"
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


@config_bp.route("/api/restart", methods=["POST"])
def restart_app():
    def do_restart():
        print(
            "[RESTART] Restarting OpenSCADA-Lite process as 'python -m openscada_lite.app' ..."
        )
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../..")
        )
        os.chdir(project_root)
        python = sys.executable
        # Use '-m openscada_lite.app' instead of the script path
        os.execl(python, python, "-m", "openscada_lite.app", *sys.argv[1:])

    threading.Thread(target=do_restart).start()
    return jsonify({"message": "Restarting OpenSCADA-Lite..."}), 200


@config_bp.route("/")
def editor():
    return render_template("editor.html")
