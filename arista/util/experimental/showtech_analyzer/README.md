# Showtech Viewer

A web-based diagnostic tool that transforms showtech logs into interactive, structured visualizations for faster troubleshooting and analysis.

## What is the purpose of this tool?

Instead of manually scanning through thousands of lines of raw text, the tool automatically structures the data, highlights critical issues, and provides an intuitive interface for exploration.

**Before:** Manually searching through raw text logs, missing critical alerts, and spending hours correlating data across multiple files.

**After:** Upload logs and immediately see:
- Parsed sections with structured data easy to read
- Anomalies in the system
- Side-by-side file comparison

## Features

### **Data Visualization**
- Converts raw logs into interactive tables and structured views
- Supports two files vieweing side by side
- Section filtering and adapatable font sizing

### **Anomaly Detection**
- Detects critical sensor values, port issues, and other hardware issues
- Detects regex patterns in the raw content
- Highlights and summarizes the anomalies in a modal with a click-to-jump navigation

## Deployment ( Locally )

### Prerequisites
- Docker installed and running on your system

>If you don't have Docker, install it from IntelligenceHub

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
If interested in more details, please refer to the deployment guide: [`docs/deployment.md`](docs/deployment.md)

---

## Technologies Used

- **Frontend:** React, JavaScript, CSS, Nginx (Docker)
- **Backend:** Python, Flask
- **Deployment:** Single Docker container

---

## Documentation
- Documentation main page is [`docs/index.md`](docs/index.md)