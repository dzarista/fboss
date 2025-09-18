#!/usr/bin/env python3
"""
Database API for Showtech Sessions
Provides CRUD operations for sessions and files in MongoDB
"""

import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
# In your db_api.py file
import os
import threading
import time
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError
from gridfs import GridFS

# Session retention period - sessions older than this will be automatically deleted
SESSION_RETENTION_DAYS = 365  # 1 year - easy to edit

class ShowtechDatabaseAPI:
    """API for managing showtech sessions and files in MongoDB"""

    def __init__(self):
        """
        Initialize database connection by building the connection string
        from environment variables.
        """
        # Read config from environment variables, providing sensible defaults.
        db_host = os.getenv("DB_HOST", "localhost")
        db_user = os.getenv("MONGO_INITDB_ROOT_USERNAME", "mongoadmin")
        db_pass = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "secret")
        db_name = os.getenv("MONGO_DATABASE", "showtech") # Use 'showtech' as the default DB name

        # Handle host:port format or default port
        if ':' in db_host:
            host_port = db_host
        else:
            host_port = f"{db_host}:27017"

        # Build the connection string dynamically
        connection_string = f"mongodb://{db_user}:{db_pass}@{host_port}/{db_name}?authSource=admin"

        print(f"INFO: Attempting to connect to MongoDB at {db_host}")

        self.client = MongoClient(connection_string)
        self.db = self.client.get_default_database()
        self.sessions_metadata = self.db.sessions_metadata
        self.session_data = self.db.session_data

        # GridFS for storing large file content
        self.fs = GridFS(self.db)

        # Collection for file metadata (lightweight references to GridFS files)
        self.file_metadata = self.db.file_metadata

        # Create indexes for better performance
        self._create_indexes()

        # Start automatic cleanup thread
        self._cleanup_thread = None
        self._cleanup_stop_event = threading.Event()
        self._start_cleanup_thread()
    
    def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Index on session_id for sessions_metadata (unique)
            self.sessions_metadata.create_index("session_id", unique=True)
            
            # Index on created_at for sorting
            self.sessions_metadata.create_index([("created_at", -1)])
            
            # Index on session_id for session_data
            self.session_data.create_index("session_id")

            # Indexes for file metadata collection
            self.file_metadata.create_index("session_id")
            self.file_metadata.create_index("file_id", unique=True)
            self.file_metadata.create_index([("session_id", 1), ("file_id", 1)])
            self.file_metadata.create_index("gridfs_id")  # Link to GridFS file
            
        except Exception as e:
            print(f"Warning: Could not create indexes: {e}")
    
    def _generate_id(self) -> str:
        """Generate a unique ID"""
        return str(uuid.uuid4())
    

    def _get_current_time(self) -> datetime:
        """Get current UTC timestamp"""
        return datetime.now(timezone.utc)

    def _serialize_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to JSON-serializable format"""
        if doc is None:
            return None

        # Create a copy to avoid modifying the original
        serialized = {}
        for key, value in doc.items():
            if key == '_id':
                # Skip MongoDB's internal _id field
                continue
            elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                # Handle lists and nested documents
                if isinstance(value, list):
                    serialized[key] = [self._serialize_document(item) if isinstance(item, dict) else item for item in value]
                elif isinstance(value, dict):
                    serialized[key] = self._serialize_document(value)
                else:
                    serialized[key] = value
            else:
                serialized[key] = value

        return serialized
    
    # ==================== SESSION OPERATIONS ====================
    
    def create_session(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new session
        
        Args:
            name: Human-readable session name
            description: Optional session description
            
        Returns:
            Dict containing session metadata
            
        Raises:
            Exception: If session creation fails
        """
        session_id = self._generate_id()
        current_time = self._get_current_time()
        
        session_metadata = {
            "session_id": session_id,
            "name": name,
            "description": description,
            "created_at": current_time,
            "last_accessed": current_time,
            "file_count": 0,
            "total_size_bytes": 0
        }
        
        try:
            # Insert session metadata
            self.sessions_metadata.insert_one(session_metadata)
            
            # Create empty session data document
            session_data = {
                "session_id": session_id,
                "files": []
            }
            self.session_data.insert_one(session_data)
            
            return self._serialize_document(session_metadata)
            
        except DuplicateKeyError:
            raise Exception(f"Session with ID {session_id} already exists")
        except PyMongoError as e:
            raise Exception(f"Database error creating session: {e}")
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session metadata by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session metadata dict or None if not found
        """
        try:
            # Update last accessed time
            self.sessions_metadata.update_one(
                {"session_id": session_id},
                {"$set": {"last_accessed": self._get_current_time()}}
            )
            
            session = self.sessions_metadata.find_one(
                {"session_id": session_id},
                {"_id": 0}  # Exclude MongoDB _id field
            )
            return self._serialize_document(session)
        except PyMongoError as e:
            print(f"Database error getting session: {e}")
            return None
    
    def list_sessions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all sessions, sorted by creation date (newest first)
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of session metadata dicts
        """
        try:
            cursor = self.sessions_metadata.find(
                {},
                {"_id": 0}
            ).sort("created_at", -1).skip(offset).limit(limit)

            sessions = list(cursor)
            return [self._serialize_document(session) for session in sessions]
        except PyMongoError as e:
            print(f"Database error listing sessions: {e}")
            return []
    
    def update_session(self, session_id: str, name: str = None, description: str = None) -> bool:
        """
        Update session metadata
        
        Args:
            session_id: Session identifier
            name: New session name (optional)
            description: New session description (optional)
            
        Returns:
            True if update successful, False otherwise
        """
        update_fields = {"last_accessed": self._get_current_time()}
        
        if name is not None:
            update_fields["name"] = name
        if description is not None:
            update_fields["description"] = description
        
        try:
            result = self.sessions_metadata.update_one(
                {"session_id": session_id},
                {"$set": update_fields}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"Database error updating session: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its files
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Delete session metadata
            metadata_result = self.sessions_metadata.delete_one({"session_id": session_id})
            
            # Delete session data
            data_result = self.session_data.delete_one({"session_id": session_id})
            
            return metadata_result.deleted_count > 0 and data_result.deleted_count > 0
        except PyMongoError as e:
            print(f"Database error deleting session: {e}")
            return False

    # ==================== FILE OPERATIONS ====================

    def add_file(self, session_id: str, filename: str, file_content: Dict[str, Any],
                 size_bytes: int = None) -> Optional[str]:
        """
        Add a file to a session using GridFS for large file storage

        Args:
            session_id: Session identifier
            filename: Original filename
            file_content: Processed file data (hostname, sections, etc.)
            size_bytes: File size in bytes (optional)

        Returns:
            File ID if successful, None otherwise
        """
        file_id = self._generate_id()
        current_time = self._get_current_time()

        # Convert file content to JSON string for GridFS storage
        file_content_json = json.dumps(file_content, ensure_ascii=False, indent=2)
        file_content_bytes = file_content_json.encode('utf-8')

        # Calculate size if not provided
        if size_bytes is None:
            size_bytes = len(file_content_bytes)

        try:
            # Verify session exists first
            session = self.session_data.find_one({"session_id": session_id})
            if not session:
                print(f"Session {session_id} not found")
                return None

            # Store file content in GridFS
            gridfs_id = self.fs.put(
                file_content_bytes,
                filename=f"{session_id}_{file_id}_{filename}",
                content_type="application/json",
                metadata={
                    "session_id": session_id,
                    "file_id": file_id,
                    "original_filename": filename,
                    "upload_date": current_time
                }
            )

            # Store file metadata in separate collection
            file_metadata = {
                "file_id": file_id,
                "session_id": session_id,
                "filename": filename,
                "upload_date": current_time,
                "size_bytes": size_bytes,
                "gridfs_id": gridfs_id,
                "content_type": "application/json"
            }

            self.file_metadata.insert_one(file_metadata)
            print(f"GridFS: Stored file {filename} with GridFS ID {gridfs_id} and file ID {file_id}")

            # Update session metadata
            self.sessions_metadata.update_one(
                {"session_id": session_id},
                {
                    "$inc": {
                        "file_count": 1,
                        "total_size_bytes": size_bytes
                    },
                    "$set": {"last_accessed": current_time}
                }
            )

            return file_id

        except PyMongoError as e:
            print(f"Database error adding file: {e}")
            return None

    def get_file(self, session_id: str, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific file from a session using GridFS

        Args:
            session_id: Session identifier
            file_id: File identifier

        Returns:
            File data dict or None if not found
        """
        try:
            # Get file metadata
            file_metadata = self.file_metadata.find_one(
                {"session_id": session_id, "file_id": file_id},
                {"_id": 0}  # Exclude MongoDB's internal _id
            )

            if not file_metadata:
                return None

            # Get file content from GridFS
            gridfs_id = file_metadata["gridfs_id"]
            try:
                gridfs_file = self.fs.get(gridfs_id)
                file_content_json = gridfs_file.read().decode('utf-8')
                file_content = json.loads(file_content_json)
            except Exception as e:
                print(f"Error reading GridFS file {gridfs_id}: {e}")
                return None

            # Build response with metadata and content
            result = {
                "file_id": file_metadata["file_id"],
                "filename": file_metadata["filename"],
                "upload_date": file_metadata["upload_date"],
                "size_bytes": file_metadata["size_bytes"]
            }

            # Merge file content into the response
            result.update(file_content)

            return self._serialize_document(result)

        except PyMongoError as e:
            print(f"Database error getting file: {e}")
            return None

        except PyMongoError as e:
            print(f"Database error getting file: {e}")
            return None

    def list_files(self, session_id: str) -> List[Dict[str, Any]]:
        """
        List all files in a session using GridFS

        Args:
            session_id: Session identifier

        Returns:
            List of file data dicts
        """
        try:
            # Get file metadata (lightweight operation)
            cursor = self.file_metadata.find(
                {"session_id": session_id},
                {"_id": 0}  # Exclude MongoDB's internal _id
            ).sort("upload_date", 1)  # Sort by upload date

            file_metadata_list = list(cursor)
            flattened_files = []

            for file_metadata in file_metadata_list:
                # Get file content from GridFS
                gridfs_id = file_metadata["gridfs_id"]
                try:
                    gridfs_file = self.fs.get(gridfs_id)
                    file_content_json = gridfs_file.read().decode('utf-8')
                    file_content = json.loads(file_content_json)

                    # Build response with metadata and content
                    result = {
                        "file_id": file_metadata["file_id"],
                        "filename": file_metadata["filename"],
                        "upload_date": file_metadata["upload_date"],
                        "size_bytes": file_metadata["size_bytes"]
                    }

                    # Merge file content into the response
                    result.update(file_content)

                    flattened_files.append(self._serialize_document(result))

                except Exception as e:
                    print(f"Error reading GridFS file {gridfs_id} for {file_metadata['filename']}: {e}")
                    # Skip this file but continue with others
                    continue

            return flattened_files

        except PyMongoError as e:
            print(f"Database error listing files: {e}")
            return []

    def update_file(self, session_id: str, file_id: str,
                   filename: str = None, file_content: Dict[str, Any] = None) -> bool:
        """
        Update file metadata or content

        Args:
            session_id: Session identifier
            file_id: File identifier
            filename: New filename (optional)
            file_content: New file content (optional)

        Returns:
            True if update successful, False otherwise
        """
        update_fields = {}

        if filename is not None:
            update_fields["files.$.filename"] = filename
        if file_content is not None:
            update_fields["files.$.file_content"] = file_content
            # Recalculate size
            update_fields["files.$.size_bytes"] = len(str(file_content).encode())

        if not update_fields:
            return False

        try:
            result = self.session_data.update_one(
                {
                    "session_id": session_id,
                    "files.file_id": file_id
                },
                {"$set": update_fields}
            )

            # Update session last accessed time
            if result.modified_count > 0:
                self.sessions_metadata.update_one(
                    {"session_id": session_id},
                    {"$set": {"last_accessed": self._get_current_time()}}
                )

            return result.modified_count > 0

        except PyMongoError as e:
            print(f"Database error updating file: {e}")
            return False

    def delete_file(self, session_id: str, file_id: str) -> bool:
        """
        Delete a file from a session

        Args:
            session_id: Session identifier
            file_id: File identifier

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Get file metadata before deletion
            file_metadata = self.file_metadata.find_one({"session_id": session_id, "file_id": file_id})
            if not file_metadata:
                return False

            file_size = file_metadata.get("size_bytes", 0)
            gridfs_id = file_metadata["gridfs_id"]

            # Delete file content from GridFS
            try:
                self.fs.delete(gridfs_id)
                print(f"GridFS: Deleted file content with GridFS ID {gridfs_id}")
            except Exception as e:
                print(f"Warning: Could not delete GridFS file {gridfs_id}: {e}")
                # Continue with metadata deletion even if GridFS deletion fails

            # Remove file metadata
            result = self.file_metadata.delete_one({"session_id": session_id, "file_id": file_id})

            if result.deleted_count > 0:
                # Update session metadata
                self.sessions_metadata.update_one(
                    {"session_id": session_id},
                    {
                        "$inc": {
                            "file_count": -1,
                            "total_size_bytes": -file_size
                        },
                        "$set": {"last_accessed": self._get_current_time()}
                    }
                )
                return True

            return False

        except PyMongoError as e:
            print(f"Database error deleting file: {e}")
            return False

    def clear_session_files(self, session_id: str) -> bool:
        """
        Remove all files from a session

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear all files from session data
            result = self.session_data.update_one(
                {"session_id": session_id},
                {"$set": {"files": []}}
            )

            if result.modified_count > 0:
                # Reset session metadata counters
                self.sessions_metadata.update_one(
                    {"session_id": session_id},
                    {
                        "$set": {
                            "file_count": 0,
                            "total_size_bytes": 0,
                            "last_accessed": self._get_current_time()
                        }
                    }
                )
                return True

            return False

        except PyMongoError as e:
            print(f"Database error clearing session files: {e}")
            return False

    # ==================== UTILITY OPERATIONS ====================

    def get_session_with_files(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete session data including metadata and files

        Args:
            session_id: Session identifier

        Returns:
            Dict with session metadata and files, or None if not found
        """
        try:
            # Get session metadata
            metadata = self.get_session(session_id)
            if not metadata:
                return None

            # Get session files
            files = self.list_files(session_id)

            return {
                "metadata": metadata,
                "files": files
            }

        except Exception as e:
            print(f"Error getting session with files: {e}")
            return None

    def search_sessions(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search sessions by name or description

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching session metadata dicts
        """
        try:
            # Case-insensitive regex search
            regex_query = {"$regex": query, "$options": "i"}

            cursor = self.sessions_metadata.find(
                {
                    "$or": [
                        {"name": regex_query},
                        {"description": regex_query}
                    ]
                },
                {"_id": 0}
            ).sort("created_at", -1).limit(limit)

            sessions = list(cursor)
            return [self._serialize_document(session) for session in sessions]

        except PyMongoError as e:
            print(f"Database error searching sessions: {e}")
            return []

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics

        Returns:
            Dict with database statistics
        """
        try:
            total_sessions = self.sessions_metadata.count_documents({})
            total_files = self.session_data.aggregate([
                {"$project": {"file_count": {"$size": "$files"}}},
                {"$group": {"_id": None, "total": {"$sum": "$file_count"}}}
            ])

            file_count = 0
            for result in total_files:
                file_count = result.get("total", 0)
                break

            # Get total size
            total_size = self.sessions_metadata.aggregate([
                {"$group": {"_id": None, "total_size": {"$sum": "$total_size_bytes"}}}
            ])

            size_bytes = 0
            for result in total_size:
                size_bytes = result.get("total_size", 0)
                break

            return {
                "total_sessions": total_sessions,
                "total_files": file_count,
                "total_size_bytes": size_bytes,
                "total_size_mb": round(size_bytes / (1024 * 1024), 2)
            }

        except PyMongoError as e:
            print(f"Database error getting stats: {e}")
            return {
                "total_sessions": 0,
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0
            }

    def _start_cleanup_thread(self):
        """Start the automatic cleanup background thread"""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
            self._cleanup_thread.start()
            print(f"INFO: Started automatic session cleanup (retention: {SESSION_RETENTION_DAYS} days)")

    def _cleanup_worker(self):
        """Background worker that periodically cleans up old sessions"""
        # Run cleanup every 24 hours
        cleanup_interval = 24 * 60 * 60  # 24 hours in seconds

        while not self._cleanup_stop_event.is_set():
            try:
                # Wait for the interval or until stop event is set
                if self._cleanup_stop_event.wait(cleanup_interval):
                    break  # Stop event was set

                # Perform cleanup
                self._cleanup_old_sessions()

            except Exception as e:
                print(f"ERROR: Automatic cleanup failed: {e}")
                # Continue running even if cleanup fails

    def _cleanup_old_sessions(self):
        """Clean up sessions older than SESSION_RETENTION_DAYS"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=SESSION_RETENTION_DAYS)

            # Find sessions to cleanup
            old_sessions = list(self.sessions_metadata.find({
                "$or": [
                    {"last_accessed": {"$lt": cutoff_date}},
                    {"last_accessed": {"$exists": False}, "created_at": {"$lt": cutoff_date}}
                ]
            }, {"session_id": 1, "name": 1, "file_count": 1}))

            if old_sessions:
                print(f"INFO: Cleaning up {len(old_sessions)} old sessions (older than {SESSION_RETENTION_DAYS} days)")

                deleted_count = 0
                for session in old_sessions:
                    try:
                        if self.delete_session(session["session_id"]):
                            deleted_count += 1
                        else:
                            print(f"WARNING: Failed to delete session {session.get('name', session['session_id'])}")
                    except Exception as e:
                        print(f"ERROR: Failed to delete session {session.get('name', session['session_id'])}: {e}")

                print(f"INFO: Successfully cleaned up {deleted_count}/{len(old_sessions)} old sessions")
            else:
                print(f"INFO: No sessions older than {SESSION_RETENTION_DAYS} days found")

        except Exception as e:
            print(f"ERROR: Session cleanup failed: {e}")

    def close(self):
        """Close database connection and stop cleanup thread"""
        # Stop cleanup thread
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_stop_event.set()
            self._cleanup_thread.join(timeout=5)

        # Close database connection
        if self.client:
            self.client.close()


