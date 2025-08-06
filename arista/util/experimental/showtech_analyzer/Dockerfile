# Multi-environment Dockerfile for Showtech Analyzer
# Supports both production and development modes
# Usage:
#   Production: docker run showtech-analyzer
#   Development: docker run showtech-analyzer dev

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY showtech-viewer/package*.json ./
RUN npm ci

COPY showtech-viewer/ ./
RUN npm run build

# Stage 2: Development frontend (for dev mode)
FROM node:18-alpine AS frontend-dev
WORKDIR /app/frontend
COPY showtech-viewer/package*.json ./
RUN npm ci
COPY showtech-viewer/ ./
EXPOSE 3000

# Stage 3: Final production/development container
FROM nginx:alpine

# Install required packages for both environments
RUN apk add --no-cache \
    python3 \
    py3-pip \
    nodejs \
    npm \
    bash \
    curl \
    supervisor

# Create app directory
WORKDIR /app

# Copy and install Python backend dependencies
COPY showtech-backend/requirements.txt ./backend/
RUN pip3 install --no-cache-dir --break-system-packages -r ./backend/requirements.txt

# Copy Python backend code
COPY showtech-backend/ ./backend/

# Copy built React frontend for production
COPY --from=frontend-build /app/frontend/build /usr/share/nginx/html

# Copy React source for development
COPY showtech-viewer/ ./frontend/

# Install frontend dependencies for development mode
WORKDIR /app/frontend
RUN npm ci

# Copy nginx configuration files
COPY showtech-viewer/nginx-prod.conf /etc/nginx/conf.d/default.conf
COPY showtech-viewer/nginx-dev.conf /etc/nginx/conf.d/dev.conf

# Copy supervisor configuration files
RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord-prod.conf /etc/supervisor/conf.d/supervisord.conf
COPY supervisord-dev.conf /etc/supervisor/conf.d/supervisord-dev.conf

# Create production startup script
RUN cat > /app/start-prod.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Showtech Analyzer in PRODUCTION mode..."

# Use production nginx config (default.conf is already the production config)
rm -f /etc/nginx/conf.d/dev.conf

# Create log directory
mkdir -p /var/log/supervisor

# Start services with supervisor
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
EOF

# Create development startup script
RUN cat > /app/start-dev.sh << 'EOF'
#!/bin/bash
echo "🔧 Starting Showtech Analyzer in DEVELOPMENT mode..."

# Use development nginx config
cp /etc/nginx/conf.d/dev.conf /etc/nginx/conf.d/default.conf

# Use development supervisor config
cp /etc/supervisor/conf.d/supervisord-dev.conf /etc/supervisor/conf.d/supervisord.conf

# Create log directory
mkdir -p /var/log/supervisor

# Start services with supervisor (with nginx using dev config)
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
EOF

# Create main entrypoint script
RUN cat > /app/entrypoint.sh << 'EOF'
#!/bin/bash

# Create data directory
mkdir -p /app/data

# Check if first argument is "dev"
if [ "$1" = "dev" ]; then
    exec /app/start-dev.sh
else
    exec /app/start-prod.sh
fi
EOF

# Make all scripts executable
RUN chmod +x /app/start-prod.sh /app/start-dev.sh /app/entrypoint.sh

# Expose ports
EXPOSE 80 3000 5001

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD []
