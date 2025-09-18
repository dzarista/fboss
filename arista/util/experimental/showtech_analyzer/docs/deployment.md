# Deployment Guide

This guide covers both Docker-based deployment (recommended) and manual local setup for the Showtech Analyzer application.

## Docker Deployment (Recommended)

> **Important:** Make sure the database is running before starting the application:
> ```bash
> cd database
> ./run-database.sh start
> ```
> Refer to [`database/README.md`](../database/README.md) for detailed database setup instructions.

Docker deployment provides a consistent, isolated environment using a **single container** that runs both frontend and backend services with different configurations for development and production.


### Prerequisites

- Docker installed and running on your system
>If you don't have Docker, install it from IntelligenceHub

### Running the Application

```bash
cd arista/util/experimental/showtech_analyzer

# Production mode (builds and runs both services)
./run.sh prod

# Development mode (with hot reloading)
./run.sh dev

# Access the application:
# Production: http://localhost (port 80)
# Development: http://localhost:3000 (React) + http://localhost/api (Flask backend on port 80)

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

### Application Monitoring

- **Health Checks**: Use `/api/status` endpoint for monitoring (status light at top right corner of app)
- **Resource Usage**: Monitor container resource consumption
- **Error Tracking**: Check application logs for errors
- **Performance Metrics**: Monitor response times and throughput
