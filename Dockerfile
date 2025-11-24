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
FROM python:3.12-slim

WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy backend + config + modules
COPY openscada_lite ./openscada_lite
COPY config ./config

# Copy built frontends from previous stage
COPY --from=frontend /app/openscada_lite/web/scada/static/frontend/dist ./openscada_lite/web/scada/static/frontend/dist
COPY --from=frontend /app/openscada_lite/web/config_editor/static/frontend/dist ./openscada_lite/web/config_editor/static/frontend/dist
COPY --from=frontend /app/openscada_lite/web/security_editor/static/frontend/dist ./openscada_lite/web/security_editor/static/frontend/dist

# Expose port (optional, Render uses $PORT)
EXPOSE 5443

CMD ["uvicorn", "openscada_lite.app:app", "--host", "0.0.0.0", "--port", "5443"]
