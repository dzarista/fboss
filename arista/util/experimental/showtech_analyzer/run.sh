#!/bin/bash

# Showtech Analyzer Docker Management Script
# Usage:
#   ./run.sh dev      # Development mode
#   ./run.sh prod     # Production mode
#   ./run.sh stop     # Stop and remove container
#   ./run.sh logs     # Show logs
#   ./run.sh help     # Show help

set -e

CONTAINER_NAME="showtech-analyzer"
IMAGE_NAME="showtech-analyzer"
MODE=${1}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to stop and remove existing container
cleanup_container() {
    if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_status "Stopping and removing existing container..."
        docker stop $CONTAINER_NAME >/dev/null 2>&1 || true
        docker rm $CONTAINER_NAME >/dev/null 2>&1 || true
        print_success "Container cleaned up"
    fi
}

# Function to build the production image
build_production_image() {
    print_status "Building Showtech Analyzer Docker image (production)..."
    docker build --no-cache -t $IMAGE_NAME . || {
        print_error "Failed to build Docker image"
        exit 1
    }
    print_success "Production Docker image built successfully"
}

# Function to build the development image
build_development_image() {
    print_status "Building Showtech Analyzer Docker image (development)..."
    docker build -t ${IMAGE_NAME}:dev --target development . || {
        print_error "Failed to build Docker image"
        exit 1
    }
    print_success "Development Docker image built successfully"
}

# Function to run in production mode
run_production() {
    print_status "Starting Showtech Analyzer in PRODUCTION mode..."

    docker run -d \
        --name $CONTAINER_NAME \
        -p 80:80 \
        --network showtech_analyzer_showtech-network \
        -v $(pwd)/database:/app/database \
        -e DB_HOST=showtech-sessions-db \
        -e MONGO_INITDB_ROOT_USERNAME=admin \
        -e MONGO_INITDB_ROOT_PASSWORD=showtech123 \
        -e MONGO_DATABASE=showtech_sessions \
        --restart unless-stopped \
        $IMAGE_NAME || {
        print_error "Failed to start container in production mode"
        exit 1
    }

    print_success "Production container started successfully!"
    echo ""
    echo "Frontend: http://localhost"
    echo "Backend API: http://localhost/api/status"

    echo ""
    echo "Management commands:"
    echo "  View logs: docker logs -f $CONTAINER_NAME"
    echo "  Stop: docker stop $CONTAINER_NAME"
    echo "  Remove: docker rm $CONTAINER_NAME"
}

# Function to run in development mode
run_development() {
    print_status "Starting Showtech Analyzer in DEVELOPMENT mode..."

    docker run -d \
        --name $CONTAINER_NAME \
        -p 80:80 \
        -p 3000:3000 \
        -v $(pwd)/showtech-viewer/src:/app/frontend/src \
        -v $(pwd)/showtech-viewer/public:/app/frontend/public \
        -v $(pwd)/showtech-backend:/app/backend \
        -v $(pwd)/database:/app/database \
        -e FLASK_ENV=development \
        -e FLASK_DEBUG=1 \
        -e CHOKIDAR_USEPOLLING=true \
        --network showtech_analyzer_showtech-network \
        -e DB_HOST=showtech-sessions-db \
        -e MONGO_INITDB_ROOT_USERNAME=admin \
        -e MONGO_INITDB_ROOT_PASSWORD=showtech123 \
        -e MONGO_DATABASE=showtech_sessions \
        --restart unless-stopped \
        ${IMAGE_NAME}:dev || {
        print_error "Failed to start container in development mode"
        exit 1
    }

    print_success "Development container started successfully!"
    echo ""
    echo "DEVELOPMENT MODE ACTIVE"
    echo "React Dev Server: http://localhost:3000 (with hot reloading)"
    echo "Flask Backend: http://localhost/api/status (with hot reloading)"

    echo "Management commands:"
    echo "  View logs: docker logs -f $CONTAINER_NAME"
    echo "  Stop: docker stop $CONTAINER_NAME"
    echo "  Remove: docker rm $CONTAINER_NAME"
}

# Function to show logs
show_logs() {
    if docker ps --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_status "Showing logs for $CONTAINER_NAME..."
        docker logs -f $CONTAINER_NAME
    else
        print_error "Container $CONTAINER_NAME is not running"
        exit 1
    fi
}

# Function to check health
check_health() {
    print_status "Checking application health..."

    # Wait longer for services to start (especially backend with database connection)
    print_status "Waiting for services to initialize..."
    sleep 10

    # Check if we're in dev or prod mode by checking which ports are exposed
    if docker port $CONTAINER_NAME | grep -q "3000/tcp"; then
        # Development mode - has both 80 and 3000 ports
        print_status "Development mode detected"

        # Check backend API with retries
        backend_ready=false
        for i in {1..6}; do
            if response=$(curl -s http://localhost/api/status 2>/dev/null); then
                print_success "✅ Backend API is responding (Flask on port 80)"

                # Check database connection status from API response
                if echo "$response" | grep -q '"database":"connected"'; then
                    print_success "✅ Database connection established"
                elif echo "$response" | grep -q '"database":"disconnected"'; then
                    print_warning "⚠️  Database connection failed - check if MongoDB is running"
                fi

                backend_ready=true
                break
            else
                if [ $i -eq 6 ]; then
                    print_error "❌ Backend API failed to start after 30 seconds"
                else
                    print_status "Backend starting... (attempt $i/6)"
                    sleep 5
                fi
            fi
        done

        if curl -s -I http://localhost:3000 >/dev/null 2>&1; then
            print_success "✅ React dev server is accessible (port 3000 with hot reloading)"
        else
            print_warning "⚠️  React dev server not accessible yet (may still be starting)"
        fi

        print_status "Note: Flask backend also has hot reloading enabled in development mode"
    else
        # Production mode - only port 80
        print_status "Production mode detected"

        # Check backend API with retries
        for i in {1..6}; do
            if response=$(curl -s http://localhost/api/status 2>/dev/null); then
                print_success "✅ Backend API is responding (Flask)"

                # Check database connection status from API response
                if echo "$response" | grep -q '"database":"connected"'; then
                    print_success "✅ Database connection established"
                elif echo "$response" | grep -q '"database":"disconnected"'; then
                    print_warning "⚠️  Database connection failed - check if MongoDB is running"
                fi

                break
            else
                if [ $i -eq 6 ]; then
                    print_error "❌ Backend API failed to start after 30 seconds"
                else
                    print_status "Backend starting... (attempt $i/6)"
                    sleep 5
                fi
            fi
        done

        if curl -s -I http://localhost >/dev/null 2>&1; then
            print_success "✅ Frontend is accessible (Flask static)"
        else
            print_warning "⚠️  Frontend not accessible yet (may still be starting)"
        fi
    fi
}

# Main script logic
if [ -z "$MODE" ]; then
    print_error "Command required. Usage: ./run.sh [dev|prod|stop|logs|help]"
    echo ""
    echo "Available commands:"
    echo "  dev   - Start in development mode (ports 80, 3000 with hot reloading for both frontend and backend)"
    echo "  prod  - Start in production mode (port 80, static files served by Flask)"
    echo "  stop  - Stop and remove container"
    echo "  logs  - Show container logs"
    echo "  help  - Show this help message"
    exit 1
fi

case $MODE in
    "dev"|"development")
        cleanup_container
        build_development_image
        run_development
        check_health
        ;;
    "prod"|"production")
        cleanup_container
        build_production_image
        run_production
        check_health
        ;;
    "stop")
        cleanup_container
        print_success "Container stopped and removed"
        ;;
    "logs")
        show_logs
        ;;
    "help"|"-h"|"--help")
        echo "Showtech Analyzer Docker Management Script"
        echo ""
        echo "Usage: ./run.sh [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  dev   - Start in development mode (ports 80, 3000 with hot reloading for both frontend and backend)"
        echo "  prod  - Start in production mode (port 80, static files served by Flask)"
        echo "  stop  - Stop and remove container"
        echo "  logs  - Show container logs"
        echo "  help  - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run.sh dev              # Development mode"
        echo "  ./run.sh prod             # Production mode"
        echo "  ./run.sh stop             # Stop container"
        echo "  ./run.sh logs             # View logs"
        ;;
    *)
        print_error "Unknown command: $MODE"
        echo ""
        echo "Available commands:"
        echo "  dev   - Start in development mode (ports 80, 3000 with hot reloading for both frontend and backend)"
        echo "  prod  - Start in production mode (port 80, static files served by Flask)"
        echo "  stop  - Stop and remove container"
        echo "  logs  - Show container logs"
        echo "  help  - Show this help message"
        exit 1
        ;;
esac
