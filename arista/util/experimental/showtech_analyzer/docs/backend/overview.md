# Backend Overview

The backend of the Showtech Viewer system is a Flask-based server responsible for handling uploaded logs, parsing them into structured data, and delivering the output to the frontend.


## Architecture

The backend accepts both individual text log files and `.zip` archives. It detects logical sections within each file, routes them to the appropriate parser, and returns structured JSON.

### Main Entry Points

- **`/api/upload` (POST):** Accepts file uploads (text or ZIP), parses them, and returns structured JSON for each log file.
For more details, read [`docs/backend/pipeline.md`](pipeline.md).
- **`/api/section-raw` (POST):** Accepts file_id and section_index, returns decompressed raw content for a specific section.
- **`/api/status` (GET):** Returns a simple JSON response for health checks and connection testing.

---

**Access Points:**
- **Production mode**: Backend API at http://localhost/api/status (via nginx)
- **Development mode**: Direct backend at http://localhost:5001/api/status