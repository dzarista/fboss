# Deployment Guide

This guide covers both Docker-based deployment (recommended) and manual local setup for the Showtech Analyzer application.

## Docker Deployment (Recommended)

Docker deployment provides a consistent, isolated environment using a **single container** that runs both frontend and backend services with different configurations for development and production.

### Prerequisites

- Docker installed and running on your system
>If you don't have Docker, install it from IntelligenceHub

### Running the Application

```bash
cd showtech-analyzer

# Production mode (builds and runs both services)
./run.sh prod

# Development mode (with hot reloading)
./run.sh dev

# Access the application:
# Production: http://localhost (port 80)
# Development: http://localhost:3000 (React) + http://localhost:5001 (API)

# Stop the application
./run.sh stop
```

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

The Docker setup uses a **single container** with 2 modes: Production and Development.

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
