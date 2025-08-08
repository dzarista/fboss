import os
import zipfile
import tempfile
import json
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

from utils.file_upload import handle_single_file_upload, handle_zip_upload

# App initialization
app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/api/status')
def get_status():
    """A single endpoint to confirm the backend is running."""
    return jsonify({"status": "Success"})

@app.route('/api/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('file')
    if not files:
        return jsonify({'error': 'No file uploaded'}), 400

    all_responses = []

    for f in files:
        try:
            if f.filename.lower().endswith('.zip'):
                all_responses.extend(handle_zip_upload(f))
            else:
                all_responses.extend(handle_single_file_upload(f))
        except Exception as e:
            # Handle unexpected errors (but not validation errors - those return empty lists)
            print(f"Unexpected error processing {f.filename}: {str(e)}")
            continue

    # If no files were successfully processed, return empty response
    if not all_responses:
        return jsonify([]), 200

    output_data = {
        'timestamp': datetime.now().isoformat(),
        'uploaded_files': [f.filename for f in files],
        'total_files_processed': len(all_responses),
        'responses': all_responses
    }

    try:
        with open('out.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Output logged to out.json - {len(all_responses)} files processed")
    except Exception as e:
        print(f"Error writing to out.json: {e}")

    return jsonify(all_responses), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)