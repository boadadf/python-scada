# ==============================
# 1. Build React frontends
# ==============================
FROM node:20 AS frontend

WORKDIR /app

# Copy package.json files first for caching
COPY openscada_lite/web/login/package*.json openscada_lite/web/login/
COPY openscada_lite/web/scada/static/frontend/package*.json openscada_lite/web/scada/static/frontend/
COPY openscada_lite/web/config_editor/static/frontend/package*.json openscada_lite/web/config_editor/static/frontend/
COPY openscada_lite/web/security_editor/static/frontend/package*.json openscada_lite/web/security_editor/static/frontend/

# Install login module
WORKDIR /app/openscada_lite/web/login
RUN npm install

# Build scada frontend
WORKDIR /app/openscada_lite/web/scada/static/frontend
RUN npm install && npm link ../../../login && npm run build

# Build config_editor frontend
WORKDIR /app/openscada_lite/web/config_editor/static/frontend
RUN npm install && npm link ../../../login && npm run build

# Build security_editor frontend
WORKDIR /app/openscada_lite/web/security_editor/static/frontend
RUN npm install && npm link ../../../login && npm run build

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

# Copy entire project (backend + frontends)
COPY . .

# Copy built frontend assets from frontend stage
COPY --from=frontend /app/openscada_lite/web/scada/static/frontend/dist ./openscada_lite/web/scada/static/frontend/dist
COPY --from=frontend /app/openscada_lite/web/config_editor/static/frontend/dist ./openscada_lite/web/config_editor/static/frontend/dist
COPY --from=frontend /app/openscada_lite/web/security_editor/static/frontend/dist ./openscada_lite/web/security_editor/static/frontend/dist

# Expose Flask port
EXPOSE 5000
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Start the Flask app
CMD ["python", "app.py"]
