# Dockerfile for Showtech Analyzer
# Usage:
#   Production: docker build -t showtech-analyzer .
#   Development: docker build -t showtech-analyzer-dev --target development .

# Stage 1: Build React frontend (for production only)
FROM node:18-alpine AS frontend-build
WORKDIR /app/showtech-viewer

# Copy package files first for better layer caching
COPY showtech-viewer/package*.json ./
RUN npm ci --only=production

# Copy source code and build
COPY showtech-viewer/ ./
RUN npm run build

# Stage 2: Production container (Flask serves static files on single port)
FROM python:3.11-alpine AS production

# Install required packages
RUN apk add --no-cache bash curl

# Create app directory structure
WORKDIR /app

# Copy and install Python backend dependencies
COPY showtech-backend/requirements.txt ./
RUN pip3 install --no-cache-dir -r ./requirements.txt

# Copy Python backend code
COPY showtech-backend/ ./

# Copy built React frontend into same directory as app.py
COPY --from=frontend-build /app/showtech-viewer/build ./build

# Create data directory
RUN mkdir -p /app/data

# Expose single port
EXPOSE 80

# Start Flask app (serves both API and static files)
CMD ["python3", "app.py"]

# Stage 3: Development container (React dev server with hot reloading + Flask backend)
FROM python:3.11-alpine AS development

# Install required packages including Node.js for React dev server
RUN apk add --no-cache bash curl nodejs npm

# Create app directory structure
WORKDIR /app

# Copy and install Python backend dependencies
COPY showtech-backend/requirements.txt ./backend/
RUN pip3 install --no-cache-dir -r ./backend/requirements.txt

# Copy Python backend code
COPY showtech-backend/ ./backend/

# Copy React source for development with hot reloading
COPY showtech-viewer/ ./frontend/
WORKDIR /app/frontend
RUN npm ci

# Create startup script for development mode with hot reloading
WORKDIR /app
RUN cat > /app/start-dev.sh << 'EOF'
#!/bin/bash
echo "🔧 Starting Showtech Analyzer in DEVELOPMENT mode with hot reloading..."

# Create data directory
mkdir -p /app/data

# Start Flask backend in background with debug mode for hot reloading
cd /app/backend
export FLASK_ENV=development
export FLASK_DEBUG=1
python3 -c "
import app
if __name__ == '__main__':
    app.app.run(host='0.0.0.0', port=80, debug=True, use_reloader=True)
" &
BACKEND_PID=$!

# Start React dev server with hot reloading
cd /app/frontend
BROWSER=none npm start &
FRONTEND_PID=$!

# Function to handle shutdown
cleanup() {
    echo 'Shutting down services...'
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
EOF

RUN chmod +x /app/start-dev.sh

# Expose ports for both Flask backend and React dev server
EXPOSE 80 3000

# Start development services with hot reloading
CMD ["/app/start-dev.sh"]

# Stage 4: Default to production
FROM production
