import os
import sys
import zipfile
import tempfile
import json
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from utils.file_upload import handle_single_file_upload, expand_and_validate_files, FileWrapper

# Add database directory to path for imports
database_path = os.path.join(os.path.dirname(__file__), '..', 'database')
sys.path.append(database_path)

try:
    from db_api import ShowtechDatabaseAPI
    print(f"✅ Successfully imported database API from {database_path}")
except ImportError as e:
    print(f"❌ Failed to import database API: {e}")
    print(f"Database path: {database_path}")
    print(f"Files in database directory: {os.listdir(database_path) if os.path.exists(database_path) else 'Directory not found'}")
    ShowtechDatabaseAPI = None

# App initialization
# Reference to directory where static app is located
app = Flask(__name__, static_folder='build')

# With this setup, CORS might not be needed for your main frontend,
# as they are now served from the same origin. It's safe to leave for other clients.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize database API
db_api = None
if ShowtechDatabaseAPI:
    try:
        # The class now handles its own connection!
        db_api = ShowtechDatabaseAPI()
        print("✅ Successfully connected to database.")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        db_api = None
else:
    print("❌ Database API not available - ShowtechDatabaseAPI not imported")

@app.route('/api/status')
def get_status():
    """A single endpoint to confirm the backend is running."""
    db_status = "connected" if db_api else "disconnected"
    return jsonify({
        "status": "Success",
        "database": db_status,
        "environment": os.getenv('FLASK_ENV', 'production')
    })

# ==================== SESSION MANAGEMENT ENDPOINTS ====================

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all sessions with metadata"""
    if not db_api:
        return jsonify({'error': 'Database not available'}), 500

    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        sessions = db_api.list_sessions(limit=limit, offset=offset)
        return jsonify({
            'sessions': sessions,
            'count': len(sessions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create a new session"""
    if not db_api:
        return jsonify({'error': 'Database not available'}), 500

    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Session name is required'}), 400

        session = db_api.create_session(
            name=data['name'],
            description=data.get('description', '')
        )
        return jsonify(session), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session with all files"""
    if not db_api:
        return jsonify({'error': 'Database not available'}), 500

    try:
        session_data = db_api.get_session_with_files(session_id)
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404

        return jsonify(session_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['PUT'])
def update_session(session_id):
    """Update session metadata"""
    if not db_api:
        return jsonify({'error': 'Database not available'}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        success = db_api.update_session(
            session_id=session_id,
            name=data.get('name'),
            description=data.get('description')
        )

        if success:
            return jsonify({'message': 'Session updated successfully'})
        else:
            return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session and all its files"""
    if not db_api:
        return jsonify({'error': 'Database not available'}), 500

    try:
        success = db_api.delete_session(session_id)
        if success:
            return jsonify({'message': 'Session deleted successfully'})
        else:
            return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/files', methods=['POST'])
def add_files_to_session(session_id):
    """Add files to an existing session"""
    if not db_api:
        return jsonify({'error': 'Database not available'}), 500

    try:
        # Check if session exists
        session = db_api.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        files = request.files.getlist('file')
        if not files:
            return jsonify({'error': 'No files uploaded'}), 400

        # Process files similar to regular upload
        all_files_to_process = expand_and_validate_files(files)
        if not all_files_to_process:
            return jsonify({'error': 'No valid files to process'}), 400

        added_files = []
        for file_obj in all_files_to_process:
            try:
                # Process the file
                result = handle_single_file_upload(file_obj)
                if result:
                    for processed_file in result:
                        # Add to database session
                        file_id = db_api.add_file(
                            session_id=session_id,
                            filename=processed_file['filename'],
                            file_content=processed_file,
                            size_bytes=len(json.dumps(processed_file))
                        )

                        if file_id:
                            processed_file['file_id'] = file_id
                            added_files.append(processed_file)

            except Exception as e:
                print(f"Error processing {file_obj.filename}: {e}")
                continue

        return jsonify({
            'message': f'Added {len(added_files)} files to session',
            'files': added_files
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>/files/<file_id>', methods=['DELETE'])
def delete_file_from_session(session_id, file_id):
    """Delete a file from a session"""
    if not db_api:
        return jsonify({'error': 'Database not available'}), 500

    try:
        success = db_api.delete_file(session_id, file_id)
        if success:
            return jsonify({'message': 'File deleted successfully'})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/search', methods=['GET'])
def search_sessions():
    """Search sessions by name or description"""
    if not db_api:
        return jsonify({'error': 'Database not available'}), 500

    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 20, type=int)

        if not query:
            return jsonify({'sessions': [], 'count': 0})

        sessions = db_api.search_sessions(query, limit=limit)
        return jsonify({
            'sessions': sessions,
            'count': len(sessions),
            'query': query
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('file')
    if not files:
        return jsonify({'error': 'No file uploaded'}), 400

    # Get session_id from form data or query parameter
    session_id = request.form.get('session_id') or request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'session_id is required'}), 400

    # Check if database is available
    if not db_api:
        return jsonify({'error': 'Database not available'}), 500

    # Verify session exists
    session = db_api.get_session(session_id)
    if not session:
        return jsonify({'error': f'Session {session_id} not found'}), 404

    # Expand and validate all files (handles both regular files and zip contents)
    all_files_to_process = expand_and_validate_files(files)

    if not all_files_to_process:
        return jsonify([]), 200

    # Process all individual files and save to database
    all_responses = []
    for file_obj in all_files_to_process:
        try:
            # Process the file content
            result = handle_single_file_upload(file_obj)
            if result and len(result) > 0:
                # Get the processed file data
                file_data = result[0]  # handle_single_file_upload returns a list

                # Add source zip info if it came from a zip
                if hasattr(file_obj, 'source_zip') and file_obj.source_zip:
                    file_data['metadata']['extracted_from'] = file_obj.source_zip

                # Calculate file size
                file_size = len(file_obj.read())
                file_obj.seek(0)  # Reset file pointer

                # Save to database
                file_id = db_api.add_file(
                    session_id=session_id,
                    filename=file_obj.filename,
                    file_content=file_data,
                    size_bytes=file_size
                )

                if file_id:
                    # Add file_id to response
                    file_data['file_id'] = file_id
                    all_responses.append(file_data)
                    print(f"Saved file {file_obj.filename} to session {session_id} with ID {file_id}")
                else:
                    print(f"Failed to save file {file_obj.filename} to database")

        except Exception as e:
            print(f"Error processing {file_obj.filename}: {e}")
            continue

    # Also save to out.json for backward compatibility
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'session_id': session_id,
        'uploaded_files': [f.filename for f in files],
        'total_files_found': len(all_files_to_process),
        'total_files_processed': len(all_responses),
        'responses': all_responses
    }

    try:
        with open('out.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Output logged to out.json - {len(all_responses)} files processed and saved to session {session_id}")
    except Exception as e:
        print(f"Error writing to out.json: {e}")

    return jsonify(all_responses), 200

@app.route('/api/count-files', methods=['POST'])
def count_files():
    """Count total files that will be processed, including files within zip archives."""
    files = request.files.getlist('file')
    if not files:
        return jsonify({'error': 'No file uploaded'}), 400

    # Use the same expansion and validation logic
    all_files_to_process = expand_and_validate_files(files)
    total_count = len(all_files_to_process)

    return jsonify({'total_count': total_count}), 200

@app.route('/api/unroll-zips', methods=['POST'])
def unroll_zips():
    """Unroll zip files and return individual file information."""
    files = request.files.getlist('file')
    if not files:
        return jsonify({'error': 'No file uploaded'}), 400

    result = {
        'files_to_remove': [],  # zip files to remove from frontend
        'files_to_add': []      # individual files to add to frontend
    }

    for f in files:
        if f.filename.lower().endswith('.zip'):
            # Mark zip for removal
            result['files_to_remove'].append(f.filename)

            # Extract individual files
            try:
                all_files_from_zip = expand_and_validate_files([f])

                for file_obj in all_files_from_zip:
                    # Create file info for frontend
                    file_info = {
                        'name': file_obj.filename,
                        'size': len(file_obj.content),
                        'type': 'text/plain',
                        'extracted_from': file_obj.source_zip,
                        'content': file_obj.content  # Store content for later upload
                    }
                    result['files_to_add'].append(file_info)

            except Exception as e:
                print(f"Error unrolling {f.filename}: {e}")
                continue

    return jsonify(result), 200


# Serve static assets with proper MIME types
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static assets (JS, CSS, etc.) with proper MIME types"""
    return send_from_directory(os.path.join(app.static_folder, 'static'), filename)

# This catch-all route serves the static frontend files.
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    This route serves the static files for the frontend application.
    - If the path is a file in the build folder, it serves that file.
    - Otherwise, it serves index.html, allowing the frontend router to handle the path.
    """
    # Handle static assets first
    if path.startswith('static/'):
        return send_from_directory(app.static_folder, path)

    # Check if it's a specific file in the build folder
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        # For all other routes, serve index.html (React Router will handle it)
        return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    # The server now hosts both the API and the static site on the same port.
    # Check if we're in development mode for hot reloading
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=80, debug=debug_mode)