"""
File abstracts file uploading and parsing.
"""

import os
import tempfile
import zipfile
import re

from .section_parsers import parse_content_by_type
from .section_utils import determine_section_type
from .log_sanity import perform_sanity_checks, get_system_map_data

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
                    'parsed_data': parsed_content,
                    'raw_content': raw_content,
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
            'parsed_data': parsed_content,
            'raw_content': raw_content,
        })

    # Perform sanity checks on all parsed sections
    sections = perform_sanity_checks(sections)

    return sections


def extract_hostname(sections):
    """Extract hostname from CPU HOSTNAME section"""
    hostname_section = next((s for s in sections if s.get('title', '') and s.get('title', '').lower() == 'cpu hostname'), None)
    if hostname_section and hostname_section.get('raw_content'):
        content = hostname_section['raw_content'].strip()
        return content if content else None
    return None

def handle_single_file_upload(file_storage):
    content = file_storage.read().decode('utf-8', errors='ignore')
    sections = parse_sections(content)

    # Get system map data
    system_map = get_system_map_data(sections)

    # Extract hostname
    hostname = extract_hostname(sections)

    file_response = {
        'name': file_storage.filename,
        'metadata': {
            'source_file': file_storage.filename,
            'total_sections': len(sections),
            'hostname': hostname
        },
        'sections': sections
    }

    # Add system_map if available
    if system_map:
        file_response['system_map'] = system_map

    return [file_response]

class FileWrapper:
    """Wrapper to make file content behave like a file storage object."""
    def __init__(self, filename, content, source_zip=None):
        self.filename = filename
        self.content = content
        self.source_zip = source_zip
        self._position = 0

    def read(self):
        return self.content.encode('utf-8')

    def seek(self, position):
        self._position = position

def is_valid_showtech_file(filename, content):
    """Check if a file is valid showtech file based on filename and content rules."""
    # Skip files that start with '.'
    if os.path.basename(filename).startswith('.'):
        return False

    # Check if content has showtech indicators in first 3 lines
    lines = content.split('\n')
    first_three_lines = '\n'.join(lines[:3]).lower()
    return "showtech" in first_three_lines

def expand_zip_file(zip_file):
    """Extract and validate files from a zip archive."""
    extracted_files = []

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, zip_file.filename)
        zip_file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        # Walk through all files and collect valid showtech files
        for root, dirs, files_in_dir in os.walk(tmpdir):
            for fname in files_in_dir:
                fpath = os.path.join(root, fname)

                # Skip the original ZIP file
                if fname == zip_file.filename:
                    continue

                try:
                    # Read content and validate file
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as file_handle:
                        content = file_handle.read()

                    if is_valid_showtech_file(fname, content):
                        # Use relative path from ZIP root for the name
                        relative_path = os.path.relpath(fpath, tmpdir)
                        display_name = relative_path.replace('\\', '/')  # Normalize path separators

                        file_wrapper = FileWrapper(display_name, content, zip_file.filename)
                        extracted_files.append(file_wrapper)

                except Exception as e:
                    print(f"Skipping file {fname}: {e}")
                    continue

    return extracted_files

def expand_and_validate_files(files):
    """Expand zip files and validate all files for showtech content."""
    all_files_to_process = []

    for f in files:
        try:
            if f.filename.lower().endswith('.zip'):
                # Expand zip file and add all valid files
                extracted_files = expand_zip_file(f)
                all_files_to_process.extend(extracted_files)
            else:
                # Handle single file
                content = f.read().decode('utf-8', errors='ignore')
                f.seek(0)  # Reset file pointer

                if is_valid_showtech_file(f.filename, content):
                    all_files_to_process.append(f)

        except Exception as e:
            print(f"Error processing {f.filename}: {str(e)}")
            continue

    return all_files_to_process

