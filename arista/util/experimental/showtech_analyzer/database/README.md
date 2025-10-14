# Showtech Viewer Sessions Database

This directory contains the MongoDB database setup for managing sessions for the app.

## Quick Start

1. **Start the database (with automatic verification):**
   ```bash
   ./run-database.sh start
   ```

2. **Check database status:**
   ```bash
   ./run-database.sh status
   ```

3. **Stop the database:**
   ```bash
   ./run-database.sh stop
   ```

## Database Structure

The database consists of three main collections plus GridFS for file storage:

### 1. `sessions_metadata` Collection
Stores metadata about each session:

```javascript
{
  session_id: "unique-session-id",           // uuid
  name: "Session Name",                      // Session name ( can be duplicated )
  created_at: ISODate("2024-01-01T00:00:00Z"), // Session creation timestamp
  last_accessed: ISODate("2024-01-01T00:00:00Z"), // Last access timestamp
  file_count: 3,                             // Number of files in the session
  total_size_bytes: 1024000,                 // Total size of all files in bytes
  description: "Session description"         // Optional description
}
```

### 2. `session_data` Collection
Stores basic session structure (files are stored separately in GridFS):

```javascript
{
  session_id: "unique-session-id",           // Links to sessions_metadata
  files: []                                  // Empty array - files stored in GridFS
}
```

### 3. `file_metadata` Collection
Stores metadata for files (actual content in GridFS):

```javascript
{
  file_id: "unique-file-id",                 // Unique identifier for the file
  session_id: "unique-session-id",           // Links to session
  filename: "original-filename.txt",         // Original filename
  upload_date: ISODate("2024-01-01T00:00:00Z"), // File upload timestamp
  size_bytes: 512000,                        // File size in bytes
  gridfs_id: ObjectId("..."),                // Reference to GridFS file
  content_type: "application/json"           // File content type
}
```

### 4. GridFS Collections (`fs.files` and `fs.chunks`)
MongoDB GridFS automatically creates these collections to store large file content:
- **`fs.files`**: File metadata and GridFS information
- **`fs.chunks`**: Actual file content split into chunks

This design allows efficient storage and retrieval of large showtech files while maintaining fast metadata queries.

## Connection Details

- **Host:** localhost
- **Port:** 27018 (external port, maps to internal 27017)
- **Username:** admin
- **Password:** showtech123
- **Database:** showtech_sessions
- **Connection String:** `mongodb://admin:showtech123@localhost:27018/showtech_sessions`

### API and Tools
- `db_api.py` - Complete Python API for database operations
- `test_api.py` - Comprehensive test suite for the API
- `db_cli.py` - Command-line interface for database management

## Sample Operations

## Database Management Commands

### Available Commands
```bash
./run-database.sh start     # Start MongoDB and verify it's ready
./run-database.sh stop      # Stop MongoDB container
./run-database.sh restart   # Restart MongoDB and verify it's ready
./run-database.sh status    # Show container status and database statistics
./run-database.sh logs      # Show container logs (live)
./run-database.sh shell     # Connect to MongoDB shell
./run-database.sh test      # Run comprehensive API tests (requires running container)
```

## Example Queries

### Insert session metadata
```javascript
db.sessions_metadata.insertOne({
  session_id: "session-001",
  name: "My Session",
  created_at: new Date(),
  last_accessed: new Date(),
  file_count: 2,
  total_size_bytes: 2048000,
  description: "Sample session"
})
```

### Insert session data
```javascript
db.session_data.insertOne({
  session_id: "session-001",
  files: [
    {
      file_id: "file-001",
      filename: "showtech.txt",
      upload_date: new Date(),
      size_bytes: 1024000,
      file_content: {
        hostname: "switch1.example.com",
        sections: ["System Info", "Interfaces", "Routing"]
      }
    }
  ]
})
```

### Query sessions
```javascript
// Find all sessions
db.sessions_metadata.find()

// Find session by ID
db.sessions_metadata.findOne({session_id: "session-001"})

// Get session files
db.session_data.findOne({session_id: "session-001"})
```

## Python API Usage

### Dependencies
```bash
pip3 install -r requirements.txt
```

### API Usage Example
```python
from db_api import ShowtechDatabaseAPI

# Initialize API
api = ShowtechDatabaseAPI()

# Create session
session = api.create_session("My Session", "Description")
session_id = session["session_id"]

# Add file
file_id = api.add_file(
    session_id=session_id,
    filename="showtech.txt",
    file_content={"hostname": "switch1", "sections": ["System", "BGP"]},
    size_bytes=1024
)

# List sessions
sessions = api.list_sessions()

# Get session with files
full_session = api.get_session_with_files(session_id)

# Clean up
api.close()
```

### Test the API
```bash
python3 test_api.py
```

## Command Line Interface

### Available Commands
```bash
# List sessions
python3 db_cli.py list

# Create session
python3 db_cli.py create "Session Name" --description "Optional description"

# Get session details
python3 db_cli.py get <session_id> --with-files

# Delete session
python3 db_cli.py delete <session_id>

# Add file to session
python3 db_cli.py add-file <session_id> /path/to/file.txt

# List files in session
python3 db_cli.py list-files <session_id>

# Delete file from session
python3 db_cli.py delete-file <session_id> <file_id>

# Search sessions
python3 db_cli.py search "query"

# Show database statistics
python3 db_cli.py stats
```

## API Reference

### Session Operations
- `create_session(name, description)` - Create new session
- `get_session(session_id)` - Get session metadata
- `list_sessions(limit, offset)` - List all sessions
- `update_session(session_id, name, description)` - Update session ( Only name is editable )
- `delete_session(session_id)` - Delete session and all files
- `search_sessions(query, limit)` - Search sessions by name/description

### File Operations
- `add_file(session_id, filename, file_content, size_bytes)` - Add file to session
- `get_file(session_id, file_id)` - Get specific file
- `list_files(session_id)` - List all files in session
- `update_file(session_id, file_id, filename, file_content)` - Update file
- `delete_file(session_id, file_id)` - Delete file from session
- `clear_session_files(session_id)` - Remove all files from session

### Utility Operations
- `get_session_with_files(session_id)` - Get session with all files
- `get_database_stats()` - Get database statistics

## Session Cleanup

The database includes automatic cleanup functionality that runs in the background. Sessions that haven't been accessed for 365 days (1 year) are automatically deleted.

### Automated Cleanup

- **Retention Period:** 365 days (configurable in `db_api.py` - `SESSION_RETENTION_DAYS`)
- **Background Process:** Cleanup runs automatically when the database API is initialized
- **Safe Operation:** Only deletes sessions that haven't been accessed within the retention period

### Manual Cleanup Testing

You can test the cleanup functionality using the API test suite:
```bash
./run-database.sh test
```

The test suite includes cleanup verification to ensure old sessions are properly removed.
