#!/bin/bash

# Showtech Sessions Database Management Script
# Usage:
#   ./run-database.sh start     # Start the database container
#   ./run-database.sh stop      # Stop the database container
#   ./run-database.sh restart   # Restart the database container
#   ./run-database.sh logs      # Show database logs
#   ./run-database.sh shell     # Connect to MongoDB shell
#   ./run-database.sh status    # Show container status
#   ./run-database.sh clean     # Remove container and volumes (WARNING: DATA LOSS)

set -e

CONTAINER_NAME="showtech-sessions-db"
IMAGE_NAME="mongo:7.0"
NETWORK_NAME="showtech_analyzer_showtech-network"
DB_PORT="27017"
EXTERNAL_PORT="27018"  # External port to avoid conflicts

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

# Function to check if container exists
container_exists() {
    docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"
}

# Function to check if container is running
container_running() {
    docker ps --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"
}

# Function to create network if it doesn't exist
create_network() {
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        print_status "Creating Docker network: $NETWORK_NAME"
        docker network create $NETWORK_NAME
        print_success "✅ Network created successfully"
    else
        print_status "✅ Network $NETWORK_NAME already exists"
    fi
}

# Function to ensure MongoDB image is available
ensure_image() {
    print_status "🚀 Removing existing MongoDB image to force fresh pull..."
    # Remove existing image to force fresh download with progress bars
    docker rmi mongo:7.0 2>/dev/null || true

    print_status "🚀 Pulling MongoDB image..."
    # This will now show full download progress since image was removed
    docker pull mongo:7.0
    print_success "✅ MongoDB image ready"
}

# Function to start the database
start_database() {
    print_status "Starting MongoDB database..."
    print_status "Ensuring Docker network '$NETWORK_NAME' exists..."
    create_network

    if container_running; then
        print_warning "Database container is already running"
        return 0
    fi

    if container_exists; then
        print_status "🚀 Starting existing database container..."
        docker start $CONTAINER_NAME
    else
        print_status "🚀 Starting new MongoDB container..."
        ensure_image

        print_status "Creating and starting database container..."
        docker run -d \
            --name $CONTAINER_NAME \
            --network $NETWORK_NAME \
            -p $EXTERNAL_PORT:$DB_PORT \
            -v showtech-db-data:/data/db \
            -e MONGO_INITDB_ROOT_USERNAME=admin \
            -e MONGO_INITDB_ROOT_PASSWORD=showtech123 \
            -e MONGO_INITDB_DATABASE=showtech_sessions \
            --restart unless-stopped \
            $IMAGE_NAME
    fi

    print_success "✅ Database container started successfully!"
    echo ""
    echo "Database Connection Details:"
    echo "  Host: localhost"
    echo "  Port: $EXTERNAL_PORT"
    echo "  Database: showtech_sessions"
    echo "  Username: admin"
    echo "  Password: showtech123"
    echo ""
    echo "Connection String: mongodb://admin:showtech123@localhost:$EXTERNAL_PORT/showtech_sessions"
    echo ""
    echo "Management commands:"
    echo "  View logs: ./run-database.sh logs"
    echo "  MongoDB shell: ./run-database.sh shell"
    echo "  Stop database: ./run-database.sh stop"
}

# Function to stop the database
stop_database() {
    if container_running; then
        print_status "Stopping database container..."
        docker stop $CONTAINER_NAME
        print_success "Database container stopped"
    else
        print_warning "Database container is not running"
    fi
}

# Function to restart the database
restart_database() {
    print_status "Restarting database..."
    stop_database
    sleep 2
    start_database
}

# Function to show logs
show_logs() {
    if container_exists; then
        print_status "Showing database logs (press Ctrl+C to exit)..."
        docker logs -f $CONTAINER_NAME
    else
        print_error "Database container does not exist"
        exit 1
    fi
}

# Function to connect to MongoDB shell
connect_shell() {
    if container_running; then
        print_status "Connecting to MongoDB shell..."
        docker exec -it $CONTAINER_NAME mongosh --username admin --password showtech123 --authenticationDatabase admin showtech_sessions
    else
        print_error "Database container is not running"
        exit 1
    fi
}

# Function to show status
show_status() {
    print_status "Database Container Status:"
    if container_exists; then
        docker ps -a --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        if container_running; then
            print_status "Testing database connection..."
            if docker exec $CONTAINER_NAME mongosh --username admin --password showtech123 --authenticationDatabase admin --eval "db.adminCommand('ping')" showtech_sessions >/dev/null 2>&1; then
                print_success "Database is responding to connections"
            else
                print_warning "Database container is running but not responding"
            fi
        fi
    else
        print_warning "Database container does not exist"
    fi
}

# Function to clean up (WARNING: DATA LOSS)
clean_database() {
    print_warning "This will remove the database container and ALL DATA will be lost!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        if container_exists; then
            print_status "Stopping and removing database container..."
            docker stop $CONTAINER_NAME 2>/dev/null || true
            docker rm $CONTAINER_NAME 2>/dev/null || true
        fi
        
        print_status "Removing database volumes..."
        docker volume rm showtech-db-data 2>/dev/null || true
        docker volume rm showtech-db-config 2>/dev/null || true
        
        print_status "Removing database image..."
        docker rmi $IMAGE_NAME 2>/dev/null || true
        
        print_success "Database cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Function to run API tests
run_tests() {
    print_status "Running comprehensive API tests..."

    if ! container_running; then
        print_error "Database container is not running. Please start it first with: $0 start"
        exit 1
    fi

    # Check if test file exists
    if [ ! -f "test_api.py" ]; then
        print_error "test_api.py not found in current directory"
        exit 1
    fi

    # Check if Python is available
    if ! command -v python3 >/dev/null 2>&1; then
        print_error "Python 3 is required to run tests"
        exit 1
    fi

    # Set environment variables for test database connection
    export DB_HOST="localhost:$EXTERNAL_PORT"
    export MONGO_INITDB_ROOT_USERNAME="admin"
    export MONGO_INITDB_ROOT_PASSWORD="showtech123"
    export MONGO_DATABASE="showtech_sessions"

    # Run the tests
    print_status "Executing test suite..."
    echo ""

    if python3 test_api.py; then
        echo ""
        print_success "✅ All tests completed successfully!"
    else
        echo ""
        print_error "❌ Some tests failed. Check the output above for details."
        exit 1
    fi
}

# Main script logic
case "${1:-}" in
    start)
        start_database
        ;;
    stop)
        stop_database
        ;;
    restart)
        restart_database
        ;;
    logs)
        show_logs
        ;;
    shell)
        connect_shell
        ;;
    status)
        show_status
        ;;
    clean)
        clean_database
        ;;
    test)
        run_tests
        ;;
    *)
        echo "Showtech Sessions Database Management"
        echo ""
        echo "Usage: $0 {start|stop|restart|logs|shell|status|clean|test}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the database container"
        echo "  stop     - Stop the database container"
        echo "  restart  - Restart the database container"
        echo "  logs     - Show database logs"
        echo "  shell    - Connect to MongoDB shell"
        echo "  status   - Show container status"
        echo "  test     - Run comprehensive API tests (requires running container)"
        echo "  clean    - Remove container and volumes (WARNING: DATA LOSS)"
        echo ""
        exit 1
        ;;
esac
