# Deployment Guide

This guide covers both Docker-based deployment (recommended) and manual local setup for the Showtech Analyzer application.

## Docker Deployment (Recommended)

Docker deployment provides a consistent, isolated environment using a **single container** that runs both frontend and backend services with different configurations for development and production.

### Prerequisites

- Docker installed and running on your system

### Quick Start

```bash
# Clone or navigate to the project directory
cd showtech_analyzer

# Production mode (builds and runs both frontend and backend)
./run.sh prod

# Development mode (with hot reloading)
./run.sh dev

# Stop the application
./run.sh stop
```

### Access Points

#### Production Mode (`./run.sh prod`)
- **Frontend**: http://localhost (optimized React build via nginx)
- **Backend API**: http://localhost/api/status (proxied through nginx)
- **Port**: Only 80 exposed (perfect for Kubernetes)

#### Development Mode (`./run.sh dev`)
- **React Dev Server**: http://localhost:3000 (with hot reloading)
- **Backend API**: http://localhost:5001/api/status (direct access)
- **Ports**: 3000 and 5001 exposed (no nginx)

### Docker Management Commands

The `run.sh` script provides convenient commands:

```bash
./run.sh prod     # Run in production mode
./run.sh dev      # Run in development mode with hot reloading
./run.sh stop     # Stop and remove container (app only)
./run.sh logs     # Show container logs
./run.sh help     # Show help message
```

**Note:** A command is required - running `./run.sh` without arguments will show an error.

### Docker Architecture

The Docker setup uses a **single container** with different modes:

#### Production Mode
- **Single Container**: nginx + Flask backend + optimized React build
- **Port 80**: nginx serves frontend and proxies API calls to Flask
- **Process Management**: Supervisor manages nginx and Flask processes
- **Optimized**: Built React app served by nginx for best performance

#### Development Mode
- **Single Container**: Flask backend + React dev server (no nginx)
- **Port 3000**: React development server with hot reloading
- **Port 5001**: Direct Flask backend access
- **Volume Mounts**: Live code changes without rebuilds


## Development vs Production Modes

### Development Mode (`./run.sh dev`)

Perfect for active development with hot reloading and direct service access:

```bash
# Start development mode
./run.sh dev

# Access services directly
# React Dev Server: http://localhost:3000 (hot reloading)
# Backend API: http://localhost:5001/api/status

# Stop when done
./run.sh stop
```

**Features:**
- Hot reloading for changes

### Production Mode (`./run.sh prod`)

Optimized for deployment with nginx proxy:

```bash
# Start production mode
./run.sh prod

# Access via nginx proxy
# Frontend: http://localhost
# Backend API: http://localhost/api/status

# Stop when done
./run.sh stop
```

**Features:**
- Optimized React build served by nginx
- Single port 80


## Manual Local Development Setup

For development or when Docker is not available, you can run the services manually.

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Git** (for cloning)

### Backend Setup

```bash
# Navigate to backend directory
cd showtech-backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python app.py
```

The backend will run on http://localhost:5001

### Frontend Setup

```bash
# Navigate to frontend directory (in a new terminal)
cd showtech-viewer

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will run on http://localhost:3000

### Manual Setup Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5001
- **API endpoints**: http://localhost:5001/api/*

### Development Workflow

1. **Start Backend First**: The backend must be running before the frontend
2. **Frontend Development**: React dev server provides hot reload
3. **API Testing**: Backend API available at http://localhost:5001/api/
4. **File Uploads**: Upload files through the frontend interface

### Troubleshooting Manual Setup

**Python Issues**
```bash
# Check Python version
python3 --version
```

#### Install pip and homebrew if missing
[Installing Homebrew & PIP on your MAC as a standard user - Google Docs.pdf](attachment:b0f6643c-a608-44b3-9ad0-bc0803227854:Installing_Homebrew__PIP_on_your_MAC_as_a_standard_user_-_Google_Docs.pdf)

**Node.js Issues**
```bash
# Check Node version
node --version
npm --version

# Install Node.js with Homebrew if missing
brew install node

# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Application Monitoring

- **Health Checks**: Use `/api/status` endpoint for monitoring (status light at top right corner of app)
- **Resource Usage**: Monitor container resource consumption
- **Error Tracking**: Check application logs for errors
- **Performance Metrics**: Monitor response times and throughput
