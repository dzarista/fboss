# Backend Overview

The backend of the Showtech Viewer system is a Flask-based server responsible for handling uploaded logs, parsing them into structured data, and delivering the output to the frontend.

**Technology**: Python, Flask, Docker


## Architecture

The backend accepts both individual text log files and `.zip` archives. It detects logical sections within each file, routes them to the appropriate parser, and returns structured JSON.

### API Endpoints

**Session Management:**
- **`GET /api/sessions`** - List all sessions
- **`POST /api/sessions`** - Create new session
- **`GET /api/sessions/{id}`** - Get session with files
- **`PUT /api/sessions/{id}`** - Update session metadata
- **`DELETE /api/sessions/{id}`** - Delete session
- **`GET /api/sessions/search`** - Search sessions

**File Operations:**
- **`POST /api/upload`** - Upload files (requires existing session_id)
- **`POST /api/sessions/{id}/files`** - Add files to existing session
- **`DELETE /api/sessions/{id}/files/{file_id}`** - Delete file from session
- **`POST /api/count-files`** - Count files in upload (including zip contents)
- **`POST /api/unroll-zips`** - Extract zip file information

**System:**
- **`GET /api/status`** - Health check and database status

**Access Points:**
- **Production**: http://localhost/api/status
- **Development**: http://localhost/api/status (port 80)