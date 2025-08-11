# Showtech Analyzer

A web-based diagnostic tool that transforms showtech logs into interactive, structured visualizations for faster troubleshooting and analysis.

## What is the purpose of this tool?

Instead of manually scanning through thousands of lines of raw text, the tool automatically structures the data, highlights critical issues, and provides an intuitive interface for exploration.

**Before:** Manually searching through raw text logs, missing critical alerts, and spending hours correlating data across multiple files.

**After:** Upload logs and immediately see:
- Critical sensor alerts highlighted in red
- Port issues automatically detected
- I2C register data with bit-field breakdowns
- Side-by-side file comparison
- Interactive tables and structured data

## Key Capabilities

### **Problem Detection**
- Automatically highlights critical sensor readings
- Identifies port configuration issues (enabled but down)
- Centralizes all alerts in a navigable error summary

### **Better Data Visualization**
- Converts raw logs into interactive tables and structured views
- Supports dual-file comparison for analysis
- Collapsible sections with persistent filtering preferences

### **Deep I2C Analysis**
- Parses PMBUS register dumps with detailed bit field breakdowns
- Interactive register exploration with command descriptions
- Supports both byte (-b) and word (-w) dump formats

## Quick Start

### Docker Deployment (Recommended)

The easiest way to get started is with Docker:

```bash
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

### Manual Development Setup

For development or when Docker is not available:

1. **Backend**: See [`docs/backend/overview.md`](docs/backend/overview.md)
2. **Frontend**: See [`docs/frontend/overview.md`](docs/frontend/overview.md)
3. Access frontend at http://localhost:3000

### Detailed Setup Instructions

For comprehensive deployment options and troubleshooting:
- **Complete Deployment Guide**: [`docs/deployment.md`](docs/deployment.md)
- **Docker vs Manual Setup**: Both options covered with full instructions


---

## Directory Structure

```bash
showtech-viewer/
├── showtech-backend/        # Flask server
├── showtech-viewer/         # React frontend
├── docs/                    # Documentation files
│   ├── backend/
│   │   ├── overview.md
│   │   ├── pipeline.md
│   │   └── pmbus_structure.md
│   └── frontend/
│       └── overview.md
├── README.md
└── ...
```

---

## Technologies

- **Frontend:** React, JavaScript, CSS3, Nginx (Docker)
- **Backend:** Python, Flask
- **Deployment:** Single Docker container
- **Parsing Tools:** PMBus spec, regex parsing, JSON conversion

---

## Documentation

- **Deployment Guide**: [`docs/deployment.md`](docs/deployment.md) - Docker and manual setup instructions
- **Main Documentation**: [`docs/index.md`](docs/index.md) - Features, architecture, and data flow
- **Backend Details**: [`docs/backend/overview.md`](docs/backend/overview.md) - Flask server and API
- **Frontend Details**: [`docs/frontend/overview.md`](docs/frontend/overview.md) - React components and architecture
- **Technical Pipeline**: [`docs/backend/pipeline.md`](docs/backend/pipeline.md) - File processing pipeline