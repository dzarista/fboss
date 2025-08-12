# Showtech Viewer - Technical Documentation

This is the main documentation page for the Showtech Fiewer tool, covering architecture, features, and data flow.

> **Full Setup Guide:** See [Deployment Guide](deployment.md) for deployment details and instructions

## System Architecture

### Component Overview

- **[Frontend (React)](frontend/overview.md)**: User interface and visualization. 
- **[Backend (Flask)](backend/overview.md)**:File processing and data transformation

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
   - Then applies appropriate parser
   - Then performs anomaly detection

3. **Response Generation**
   - Structured file data returned to frontend

4. **Frontend Rendering**

### Data Structures

#### Section Object Structure
```json
{
  "title": "Section Name",
  "section_type": "table|i2c_dump|key_value|lspci|raw",
  "parsed_data": {
    // Specific structure based on section type
    // For auto-compressed sections: {"type": "auto_compressed", "message": "...", "content_size": 12345}
  },
  "raw_content_compressed": "base64-encoded-gzipped-content",
  "auto_compressed": false
}
```
## Feature Documentation

### Anomaly Detection System

#### Backend Detection
- **Critical Sensors**: Scans table values for "critical" strings
- **Port Status**: Identifies enabled+present+down port combinations
- **I2C Issues**: (Future) highlights unexpected values of registers

#### Frontend Highlighting
- **Visual Indicators**: Color-coded table rows
- **Error Summary**: Collapsible modal with categorized issues
- **Navigation**: Click-to-jump functionality for quick issue location

## Development Guidelines

### Adding New Parsers
1. **Define Section Type**: Add to `SECTION_TYPES` in `section_utils.py`
2. **Implement Parser**: Create parser function in `section_parsers.py`
3. **Add Frontend Support**: Update rendering logic in `Content.js`

### Adding Anomaly Detection
1. **Backend Logic**: Add detection function in `log_sanity.py`
2. **Data Structure**: Include anomaly info in parsed output
3. **Frontend Display**: Update error detection and styling
