import os
import zipfile
import tempfile
import json
import uuid
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

from utils.file_upload import handle_single_file_upload, expand_and_validate_files, FileWrapper, decompress_raw_content

# App initialization
app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}})

# In-memory storage for processed files (for raw data access)
# In production, this should be replaced with a proper cache/database
processed_files_cache = {}

@app.route('/api/status')
def get_status():
    """A single endpoint to confirm the backend is running."""
    return jsonify({"status": "Success"})


@app.route('/api/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('file')
    if not files:
        return jsonify({'error': 'No file uploaded'}), 400

    # Expand and validate all files (handles both regular files and zip contents)
    all_files_to_process = expand_and_validate_files(files)

    if not all_files_to_process:
        return jsonify([]), 200

    # Process all individual files
    all_responses = []
    for file_obj in all_files_to_process:
        try:
            result = handle_single_file_upload(file_obj)
            if result:
                # Add unique file ID and store in cache for raw data access
                for item in result:
                    file_id = str(uuid.uuid4())
                    item['file_id'] = file_id

                    # Store in cache for raw data access
                    processed_files_cache[file_id] = item

                    # Add source zip info if it came from a zip
                    if hasattr(file_obj, 'source_zip') and file_obj.source_zip:
                        item['metadata']['extracted_from'] = file_obj.source_zip
                all_responses.extend(result)
        except Exception as e:
            print(f"Error processing {file_obj.filename}: {e}")
            continue

    output_data = {
        'timestamp': datetime.now().isoformat(),
        'uploaded_files': [f.filename for f in files],
        'total_files_found': len(all_files_to_process),
        'total_files_processed': len(all_responses),
        'responses': all_responses
    }

    try:
        with open('out.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Output logged to out.json - {len(all_responses)} files processed from {len(all_files_to_process)} found")
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

@app.route('/api/section-raw', methods=['POST'])
def get_section_raw():
    """Get raw (decompressed) content for a specific section."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    file_id = data.get('file_id')
    section_index = data.get('section_index')

    if not file_id or section_index is None:
        return jsonify({'error': 'file_id and section_index are required'}), 400

    # Check if file exists in cache
    if file_id not in processed_files_cache:
        return jsonify({'error': 'File not found in cache'}), 404

    file_data = processed_files_cache[file_id]
    sections = file_data.get('sections', [])

    # Check if section index is valid
    if section_index < 0 or section_index >= len(sections):
        return jsonify({'error': 'Invalid section index'}), 400

    section = sections[section_index]
    compressed_raw = section.get('raw_content_compressed', '')

    # Decompress the raw content
    raw_content = decompress_raw_content(compressed_raw)

    return jsonify({
        'raw_content': raw_content,
        'section_title': section.get('title', ''),
        'section_type': section.get('section_type', '')
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)