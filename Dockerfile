# ==========================================
# 1. Build all React frontends in place
# ==========================================
FROM node:18 AS frontend

WORKDIR /app

# Copy only the frontend sources first for caching
COPY openscada_lite/web/scada/static/frontend/package*.json openscada_lite/web/scada/static/frontend/
COPY openscada_lite/web/config_editor/static/frontend/package*.json openscada_lite/web/config_editor/static/frontend/
COPY openscada_lite/web/security_editor/static/frontend/package*.json openscada_lite/web/security_editor/static/frontend/
COPY openscada_lite/web/login/package*.json openscada_lite/web/login/

# Install and build each app
WORKDIR /app/openscada_lite/web/login
RUN npm install

WORKDIR /app/openscada_lite/web/scada/static/frontend
RUN npm install && npm link ../../login && npm run build || npm run build:prod

WORKDIR /app/openscada_lite/web/config_editor/static/frontend
RUN npm install && npm link ../../login && npm run build || npm run build:prod

WORKDIR /app/openscada_lite/web/security_editor/static/frontend
RUN npm install && npm link ../../login && npm run build || npm run build:prod


# ==========================================
# 2. Python backend (Flask)
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Install OS dependencies if needed for Flask-SocketIO
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project (including built frontends)
COPY . .

# Copy built frontend artifacts from previous stage
COPY --from=frontend /app/openscada_lite/web/scada/static/frontend/dist ./openscada_lite/web/scada/static/frontend/dist
COPY --from=frontend /app/openscada_lite/web/config_editor/static/frontend/dist ./openscada_lite/web/config_editor/static/frontend/dist
COPY --from=frontend /app/openscada_lite/web/security_editor/static/frontend/dist ./openscada_lite/web/security_editor/static/frontend/dist

# Expose Flask port
EXPOSE 5000
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Start the Flask app (with WebSocket support)
CMD ["python", "app.py"]