# Showtech Analyzer - Technical Documentation

This is the main technical documentation for the Showtech Analyzer system, covering architecture, features, and data flow.

## Quick Start

### Production Deployment
```bash
./run.sh prod
# Access at http://localhost
```

### Development Mode (Hot Reloading)
```bash
./run.sh dev
# Frontend: http://localhost:3000 (with live reload)
# Backend: http://localhost:5001/api/status
```

> **Full Setup Guide:** See [Deployment Guide](deployment.md) for complete Docker and manual setup instructions

## System Architecture

### High-Level Overview

```
┌─────────────────┐    HTTP/JSON    ┌─────────────────┐
│                 │ ──────────────► │                 │
│  React Frontend │                 │  Flask Backend  │
│                 │ ◄────────────── │                 │
└─────────────────┘                 └─────────────────┘
         │                                   │
         │                                   │
    ┌────▼────┐                         ┌────▼────┐
    │ Browser │                         │  File   │
    │ Storage │                         │ Parsing │
    └─────────┘                         └─────────┘
```

### Component Overview

**Frontend (React)** - User interface and visualization
**Backend (Flask)** - File processing and data transformation

> **Deployment:** See [Deployment Guide](deployment.md) for Docker and manual setup options

## Data Flow Architecture

### Upload and Processing Flow

1. **File Upload**
   - User drags/drops files or uses browse button
   - Frontend sends multipart form data to `/api/upload`
   - Backend determines file type (single file vs ZIP)

2. **File Processing**
   - Backend extracts and reads file contents
   - Then splits content into logical sections
   - Then identifies type for each section

3. **Section Parsing**
   - Table Parser: ASCII tables → structured headers/rows
   - I2C Parser: Hex dumps → PMBUS register analysis
   - Key-Value Parser: Colon-delimited → dictionary format
   - LSPCI Parser: Device listings → structured device info

4. **Response Generation**
   - Parsed data wrapped in JSON with metadata
   - Anomaly detection results included
   - Frontend receives structured response

5. **Frontend Rendering**
   - JSON data stored in React state and browser cache
   - Components render appropriate visualizations
   - Error detection highlights critical issues

### Data Structures

#### Section Object Structure
```json
{
  "title": "Section Name",
  "section_type": "table|i2c_dump|key_value|lspci|raw",
  "parsed_data": {
    // Specific structure based on section type
  }
}
```

## Feature Documentation

### Anomaly Detection System

#### Backend Detection
- **Critical Sensors**: Scans table values for "critical" strings
- **Port Status**: Identifies enabled+present+down port combinations
- **I2C Issues**: Detects communication failures and invalid values

#### Frontend Highlighting
- **Visual Indicators**: Color-coded table rows (red=critical, grey=disabled)
- **Error Summary**: Collapsible modal with categorized issues
- **Navigation**: Click-to-jump functionality for quick issue location

## Development Guidelines

### Adding New Parsers
1. **Define Section Type**: Add to `SECTION_TYPES` in `section_utils.py`
2. **Implement Parser**: Create parser function in `section_parsers.py`
3. **Add Frontend Support**: Update rendering logic in `Content.js`
4. **Test Integration**: Verify end-to-end functionality

### Adding Anomaly Detection
1. **Backend Logic**: Extend detection in parser functions
2. **Data Structure**: Include anomaly info in parsed output
3. **Frontend Display**: Update error detection and styling
4. **User Experience**: Add navigation and summary features

## Related Documentation

- **[Deployment Guide](deployment.md)** - Docker and manual setup instructions with troubleshooting
- **[Anomaly Detection](anomaly-detection.md)** - Anomaly detection system and adding new detection types
- **[Backend Architecture & Setup](backend/overview.md)** - Flask server, API endpoints, and infrastructure
- **[Frontend Architecture & Setup](frontend/overview.md)** - React components, state management, and UI
- **[Processing Pipeline](backend/pipeline.md)** - Detailed file parsing and transformation logic
- **[PMBUS Structure](backend/pmbus_structure.md)** - I2C register definitions and schemas
