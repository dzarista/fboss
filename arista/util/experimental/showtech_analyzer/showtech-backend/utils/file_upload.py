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

    # Quick check: look at first 3 lines for showtech indicators
    lines = content.split('\n')
    first_three_lines = '\n'.join(lines[:3]).lower()

    # Check if first 3 lines contain showtech indicators
    showtech_indicators = ['showtech', 'show-tech', 'show version', 'show platform', 'fboss2', 'wedge_qsfp_util']
    has_showtech_indicator = any(indicator in first_three_lines for indicator in showtech_indicators)

    if not has_showtech_indicator:
        print(f"Skipping file {file_storage.filename}: no showtech indicators in first 3 lines")
        return []

    sections = parse_sections(content)

    # Validate that the file has sufficient showtech content (at least 3 sections)
    if not sections or len(sections) < 3:
        print(f"Skipping file {file_storage.filename}: insufficient sections ({len(sections)} found, minimum 3 required)")
        return []

    return [{
        'name': file_storage.filename,
        'metadata': {
            'source_file': file_storage.filename,
            'total_sections': len(sections)
        },
        'sections': sections
    }]

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

def is_showtech_content(content):
    """Check if content has showtech indicators in first 3 lines."""
    lines = content.split('\n')
    first_three_lines = '\n'.join(lines[:3]).lower()
    return "showtech" in first_three_lines

def expand_and_validate_files(files):
    """Expand zip files and validate all files for showtech content."""
    all_files_to_process = []

    for f in files:
        try:
            if f.filename.lower().endswith('.zip'):
                # Expand zip file
                with tempfile.TemporaryDirectory() as tmpdir:
                    zip_path = os.path.join(tmpdir, f.filename)
                    f.save(zip_path)

                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(tmpdir)

                    # Walk through all files and collect valid showtech files
                    for root, dirs, files_in_dir in os.walk(tmpdir):
                        for fname in files_in_dir:
                            fpath = os.path.join(root, fname)

                            # Skip the original ZIP file
                            if fname == f.filename:
                                continue

                            # Skip files that start with '.'
                            if os.path.basename(fname).startswith('.'):
                                continue

                            try:
                                # Read content and check for showtech
                                with open(fpath, 'r', encoding='utf-8', errors='ignore') as file_handle:
                                    content = file_handle.read()

                                if is_showtech_content(content):
                                    # Use relative path from ZIP root for the name
                                    relative_path = os.path.relpath(fpath, tmpdir)
                                    display_name = relative_path.replace('\\', '/')  # Normalize path separators

                                    file_wrapper = FileWrapper(display_name, content, f.filename)
                                    all_files_to_process.append(file_wrapper)

                            except Exception as e:
                                print(f"Skipping file {fname}: {e}")
                                continue
            else:
                # Handle single file
                # Skip files that start with '.'
                if os.path.basename(f.filename).startswith('.'):
                    continue

                content = f.read().decode('utf-8', errors='ignore')
                f.seek(0)  # Reset file pointer

                if is_showtech_content(content):
                    all_files_to_process.append(f)

        except Exception as e:
            print(f"Error processing {f.filename}: {str(e)}")
            continue

    return all_files_to_process

