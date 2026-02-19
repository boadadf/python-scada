#!/bin/bash
# deploy.sh - Robust SCADA deployer for NFS/SD/USB

# ---------------------------
# Absolute paths for commands
# ---------------------------
BASH=/bin/bash
MKDIR=/bin/mkdir
DATE_BIN=/bin/date
GIT=/usr/bin/git
DOCKER=/usr/bin/docker
ECHO=/bin/echo

# ---------------------------
# Logging
# ---------------------------
LOG_DIR=/opt/deployer/logs
$MKDIR -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/deploy-$($DATE_BIN +%Y%m%d-%H%M%S).log"
exec >> "$LOG_FILE" 2>&1
set -x  # Print commands
set -e  # Exit on error

$ECHO "=== DEPLOY STARTED ==="

# ---------------------------
# Configuration
# ---------------------------
DATE=$($DATE_BIN +%Y%m%d-%H%M%S)
REGISTRY="localhost:5000"
REPO="python-scada"
IMAGE="$REGISTRY/$REPO:$DATE"
REPO_DIR="/opt/deployer/repo"
CONFIG_DIR="/opt/deployer/config"
DEPLOY_KEY="/home/orangepi/.ssh/id_ed25519"

# ---------------------------
# SSH agent and deploy key
# ---------------------------
if ! ssh-add -l >/dev/null 2>&1; then
    $ECHO "Starting temporary ssh-agent and adding key..."
    eval $(ssh-agent -s)
    ssh-add "$DEPLOY_KEY"
fi

# Make repo safe for git
$GIT config --global --add safe.directory "$REPO_DIR"

# ---------------------------
# Pull or clone repo safely
# ---------------------------
if [ ! -d "$REPO_DIR/.git" ]; then
    $ECHO "Directory empty or missing git repo — cleaning and cloning..."
    rm -rf "$REPO_DIR"
    $MKDIR -p "$REPO_DIR"
    $GIT clone git@github.com:boadadf/python-scada.git "$REPO_DIR"
else
    $ECHO "Repository exists, updating..."
    cd "$REPO_DIR"
    $GIT fetch --all --prune
    $GIT reset --hard origin/HEAD
fi

cd "$REPO_DIR"

# ---------------------------
# Build Docker image
# ---------------------------
$ECHO "=== Building Docker image: $IMAGE ==="
$DOCKER build -t "$IMAGE" .

# ---------------------------
# Push Docker image
# ---------------------------
$ECHO "=== Pushing Docker image ==="
$DOCKER push "$IMAGE"

# ---------------------------
# Cleanup old images (keep last 5)
# ---------------------------
$ECHO "=== Cleaning old images (keep last 5) ==="
OLD_IMAGES=$($DOCKER images "$REGISTRY/$REPO" --format "{{.Repository}}:{{.Tag}}" | sort | head -n -5)
if [ -n "$OLD_IMAGES" ]; then
    $ECHO "$OLD_IMAGES"
    echo "$OLD_IMAGES" | xargs -r $DOCKER rmi
else
    $ECHO "No old images to remove."
fi

# ---------------------------
# Restart container
# ---------------------------
$ECHO "=== Restarting container ==="
$DOCKER stop python-scada || $ECHO "No container to stop"
$DOCKER rm python-scada || $ECHO "No container to remove"
$DOCKER run -d --name python-scada -v /var/run/docker.sock:/var/run/docker.sock -v "$CONFIG_DIR":/config --restart=always -p 5443:5443 "$IMAGE"

$ECHO "=== DEPLOY COMPLETE ==="
$ECHO "Log saved to $LOG_FILE"

# ---------------------------
# Cleanup trigger
# ---------------------------
rm -f /opt/deployer/deploy.trigger

