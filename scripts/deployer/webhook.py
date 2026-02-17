#!/usr/bin/env python3
from flask import Flask, request
import os, hmac, hashlib

SECRET = os.environ.get("GITHUB_SECRET", "").encode()
BRANCH = "refs/heads/master"
TRIGGER_FILE = "/opt/deployer/deploy.trigger"

app = Flask(__name__)

def verify_signature(payload, signature_header):
    if not SECRET or not signature_header:
        return False
    mac = hmac.new(SECRET, msg=payload, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected, signature_header)

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(request.data, signature):
        return "Invalid signature", 403

    event = request.headers.get("X-GitHub-Event", "")
    data = request.json or {}
    ref = data.get("ref", None)

    # Debug log
    with open("/opt/deployer/webhook-debug.log", "a") as f:
        f.write(f"EVENT={event}, REF={ref}\n")

    if event == "ping":
        return "pong", 200

    # Make branch check robust
    BRANCHES = ["refs/heads/master", "refs/heads/main"]
    if event == "push" and ref in BRANCHES:
        with open("/opt/deployer/deploy.trigger", "w") as f:
            f.write("deploy\n")
        with open("/opt/deployer/webhook-debug.log", "a") as f:
            f.write("Trigger file created\n")
        return "Deploy triggered", 200

    with open("/opt/deployer/webhook-debug.log", "a") as f:
        f.write("Event ignored\n")
    return f"Ignored event={event}, ref={ref}", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)

