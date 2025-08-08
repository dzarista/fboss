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

def is_showtech_file(filename):
    """Check if a file is likely a showtech file based on simple rules."""
    # Skip files that start with '.'
    if os.path.basename(filename).startswith('.'):
        return False

    return True

def validate_showtech_content(file_path):
    """
    Validate that a file has sufficient showtech content.
    Requires at least 3 sections to be considered valid.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Parse the file to get sections
        sections = parse_sections(content)

        # Simply check if we have at least 3 sections
        return sections and len(sections) >= 3

    except Exception as e:
        print(f"Error validating showtech content: {e}")
        return False

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

                # Only process files that look like showtech files
                if not is_showtech_file(fname):
                    continue

                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Quick check: look at first 3 lines for showtech indicators
                    lines = content.split('\n')
                    first_three_lines = '\n'.join(lines[:3]).lower()

                    # Check if first 3 lines contain showtech indicators
                    showtech_indicators = ['showtech', 'show-tech', 'show version', 'show platform', 'fboss2', 'wedge_qsfp_util']
                    has_showtech_indicator = any(indicator in first_three_lines for indicator in showtech_indicators)

                    if not has_showtech_indicator:
                        print(f"Skipping file {fname}: no showtech indicators in first 3 lines")
                        continue

                    # Only process files that actually contain showtech-like content
                    # Require at least 3 sections to be considered valid showtech
                    sections = parse_sections(content)
                    if sections and len(sections) >= 3:
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