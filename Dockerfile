# ==============================
# 1. Build React frontends
# ==============================
FROM node:20 AS frontend

WORKDIR /app

# ------------------------------
# SCADA frontend
# ------------------------------
WORKDIR /app/openscada_lite/web/scada/static/frontend
COPY openscada_lite/web/scada/static/frontend/package*.json ./
RUN npm install
COPY openscada_lite/web/scada/static/frontend/ ./
COPY openscada_lite/web/login ./node_modules/login
RUN npm run build

# ------------------------------
# Config Editor frontend
# ------------------------------
WORKDIR /app/openscada_lite/web/config_editor/static/frontend
COPY openscada_lite/web/config_editor/static/frontend/package*.json ./
RUN npm install
COPY openscada_lite/web/config_editor/static/frontend/ ./
COPY openscada_lite/web/login ./node_modules/login
RUN npm run build

# ------------------------------
# Security Editor frontend
# ------------------------------
WORKDIR /app/openscada_lite/web/security_editor/static/frontend
COPY openscada_lite/web/security_editor/static/frontend/package*.json ./
RUN npm install
COPY openscada_lite/web/security_editor/static/frontend/ ./
COPY openscada_lite/web/login ./node_modules/login
RUN npm run build

# ==============================
# 2. Python backend
# ==============================
FROM python:3.11-slim

WORKDIR /app

# Install OS dependencies for Flask/Gunicorn
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy backend + config + modules
COPY openscada_lite ./openscada_lite
COPY app.py ./app.py  # if your main Flask file is at root
COPY config ./config
COPY test ./test

# Copy built frontends from previous stage
COPY --from=frontend /app/openscada_lite/web/scada/static/frontend/dist ./openscada_lite/web/scada/static/frontend/dist
COPY --from=frontend /app/openscada_lite/web/config_editor/static/frontend/dist ./openscada_lite/web/config_editor/static/frontend/dist
COPY --from=frontend /app/openscada_lite/web/security_editor/static/frontend/dist ./openscada_lite/web/security_editor/static/frontend/dist

# Expose port (optional)
EXPOSE 5000

# Start Flask via Gunicorn with Render $PORT
CMD ["gunicorn", "-b", "0.0.0.0:$PORT", "openscada_lite.app:app"]
