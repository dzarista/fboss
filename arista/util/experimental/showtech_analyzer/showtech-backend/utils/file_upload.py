"""
File abstracts file uploading and parsing.
"""

import os
import tempfile
import zipfile
import re
from .section_parsers import parse_content_by_type
from .section_utils import determine_section_type
from .log_sanity import perform_sanity_checks

def is_showtech_file(filename=None, content=None, file_path=None):
    """
    Simple check if a file is a showtech file.

    Args:
        filename (str, optional): The filename to check
        content (str, optional): The file content to check
        file_path (str, optional): Path to file to read and validate

    Returns:
        bool: True if file appears to be a showtech file, False otherwise
    """
    # Basic filename checks
    if filename:
        # Skip files that start with '.'
        if os.path.basename(filename).startswith('.'):
            return False

    # If file_path is provided, read the content
    if file_path and not content:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return False

    # Content-based validation
    if content:
        # Quick check: look at first 3 lines for showtech
        lines = content.split('\n')
        first_three_lines = '\n'.join(lines[:3]).lower()

        if "showtech" not in first_three_lines:
            return False

    # If only filename provided and no content checks needed, assume it's valid
    return True

def parse_sections(text):
    lines = text.splitlines()
    sections = []
    current = {'title': None, 'content': []}

    for line in lines:
        stripped = line.strip()
        if re.fullmatch(r"#+", stripped):
            continue
        if re.match(r"^#+\s*\S.*\S\s*#+$", stripped):
            if current['title'] or current['content']:
                raw_content = '\n'.join(current['content']).rstrip()
                section_type = determine_section_type(current['title'])
                parsed_content = parse_content_by_type(section_type, raw_content)

                sections.append({
                    'title': current['title'],
                    'section_type': section_type,
                    'parsed_data': parsed_content
                })
            title = re.sub(r"^#+", "", stripped)
            title = re.sub(r"#+$", "", title).strip()
            current = {'title': title, 'content': []}
        else:
            current['content'].append(line)

    if current['title'] or current['content']:
        raw_content = '\n'.join(current['content']).rstrip()
        section_type = determine_section_type(current['title'])
        parsed_content = parse_content_by_type(section_type, raw_content)

        sections.append({
            'title': current['title'],
            'section_type': section_type,
            'parsed_data': parsed_content
        })

    # Perform sanity checks on all parsed sections
    sections = perform_sanity_checks(sections)

    return sections


def handle_single_file_upload(file_storage):
    content = file_storage.read().decode('utf-8', errors='ignore')

    if not is_showtech_file(filename=file_storage.filename, content=content):
        print(f"Skipping file {file_storage.filename}: not a valid showtech file")
        return []

    # Parse sections (we know it's valid from the check above)
    sections = parse_sections(content)

    return [{
        'name': file_storage.filename,
        'metadata': {
            'source_file': file_storage.filename,
            'total_sections': len(sections)
        },
        'sections': sections
    }]



def handle_zip_upload(file_storage):
    responses = []
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, file_storage.filename)
        file_storage.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        # Walk through all files and subdirectories
        for root, dirs, files in os.walk(tmpdir):
            for fname in files:
                fpath = os.path.join(root, fname)

                # Skip the original ZIP file
                if fname == file_storage.filename:
                    continue

                # Check if this is a valid showtech file (filename + content validation)
                if not is_showtech_file(filename=fname, file_path=fpath):
                    continue

                try:
                    # Read content and parse sections (we know it's valid from the check above)
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    sections = parse_sections(content)

                    # Use relative path from ZIP root for the name
                    relative_path = os.path.relpath(fpath, tmpdir)
                    display_name = relative_path.replace('\\', '/')  # Normalize path separators

                    responses.append({
                        'name': display_name,
                        'metadata': {
                            'source_file': display_name,
                            'total_sections': len(sections),
                            'extracted_from': file_storage.filename
                        },
                        'sections': sections
                    })
                except Exception as e:
                    # Skip files that can't be read or processed
                    print(f"Skipping file {fname}: {e}")
                    continue

    return responses