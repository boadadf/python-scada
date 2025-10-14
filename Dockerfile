# ==============================
# 1. Build React frontends
# ==============================
FROM node:20 AS frontend

WORKDIR /app

# ------------------------------
# Build scada frontend
# ------------------------------
WORKDIR /app/openscada_lite/web/scada/static/frontend
# Copy package.json for caching
COPY openscada_lite/web/scada/static/frontend/package*.json ./
RUN npm install
# Copy frontend source
COPY openscada_lite/web/scada/static/frontend/ ./
# Copy login module into node_modules so Webpack can resolve it
COPY openscada_lite/web/login ./node_modules/login
# Build frontend
RUN npm run build

# ------------------------------
# Build config_editor frontend
# ------------------------------
WORKDIR /app/openscada_lite/web/config_editor/static/frontend
COPY openscada_lite/web/config_editor/static/frontend/package*.json ./
RUN npm install
COPY openscada_lite/web/config_editor/static/frontend/ ./
COPY openscada_lite/web/login ./node_modules/login
RUN npm run build

# ------------------------------
# Build security_editor frontend
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

# Install OS dependencies for Flask-SocketIO
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend + other files
COPY . .

# Copy built frontends from previous stage
COPY --from=frontend /app/openscada_lite/web/scada/static/frontend/dist ./openscada_lite/web/scada/static/frontend/dist
COPY --from=frontend /app/openscada_lite/web/config_editor/static/frontend/dist ./openscada_lite/web/config_editor/static/frontend/dist
COPY --from=frontend /app/openscada_lite/web/security_editor/static/frontend/dist ./openscada_lite/web/security_editor/static/frontend/dist

# Expose Flask port
EXPOSE 5000
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Start Flask app
CMD ["python", "app.py"]
