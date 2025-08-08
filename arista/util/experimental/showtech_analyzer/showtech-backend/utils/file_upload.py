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
    sections = parse_sections(content)
    return [{
        'name': file_storage.filename,
        'metadata': {
            'source_file': file_storage.filename,
            'total_sections': len(sections)
        },
        'sections': sections
    }]

def is_showtech_file(filename):
    """Check if a file is likely a showtech file based on name and extension."""
    name = filename.lower()

    # Skip common non-showtech files
    skip_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx',
                      '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.tar', '.gz'}
    skip_names = {'readme', 'license', 'changelog', 'install', 'setup'}

    # Check if file should be skipped
    if any(name.endswith(ext) for ext in skip_extensions):
        return False
    if any(skip_name in name for skip_name in skip_names):
        return False

    # Accept files with showtech-related keywords
    showtech_keywords = ['showtech', 'show-tech', 'support', 'debug', 'diag', 'log']
    if any(keyword in name for keyword in showtech_keywords):
        return True

    # Accept common text file extensions
    text_extensions = {'.txt', '.log', '.out', '.cfg', '.conf'}
    if any(name.endswith(ext) for ext in text_extensions):
        return True

    # Accept files without extensions (common for showtech files)
    if '.' not in os.path.basename(name):
        return True

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

                    # Only process files that actually contain showtech-like content
                    sections = parse_sections(content)
                    if sections and len(sections) > 0:
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