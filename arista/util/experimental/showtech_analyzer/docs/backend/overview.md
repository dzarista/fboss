# Backend Overview

The backend of the Showtech Viewer system is a Flask-based server responsible for handling uploaded logs, parsing them into structured data, and delivering the output to the frontend.


## Architecture

The backend accepts both individual text log files and `.zip` archives. It detects logical sections within each file, routes them to the appropriate parser, and returns structured JSON.

### Main Entry Points

- **`/api/upload` (POST):** Accepts file uploads (text or ZIP), parses them, and returns structured JSON for each log file.
For more details, read [`docs/backend/pipeline.md`](pipeline.md).
- **`/api/status` (GET):** Returns a simple JSON response for health checks and connection testing.

---

## Setup Instructions

### Docker Setup (Recommended)

The easiest way to run the backend is with Docker:

```bash
# From the project root directory
# Production mode (backend available via nginx proxy)
./run.sh prod

# Development mode (direct backend access)
./run.sh dev
```

**Access Points:**
- **Production mode**: Backend API at http://localhost/api/status (via nginx)
- **Development mode**: Direct backend at http://localhost:5001/api/status

### Manual Setup

For development or when Docker is not available:

```bash
cd showtech-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

> **Note:** For complete deployment instructions including troubleshooting, see [`../deployment.md`](../deployment.md)