"""
File abstracts file uploading and parsing.
"""

import os
import tempfile
import zipfile
import re
import json

from .section_parsers import parse_content_by_type
from .section_utils import determine_section_type
from .log_sanity import perform_sanity_checks, get_system_map_data


# ---------------------------
# Platform config helpers
# ---------------------------

def _configs_root():
    # ../configs relative to this file
    return os.path.join(os.path.dirname(__file__), '..', 'configs')


def _load_platform_config(product_name: str):
    """
    Load platform configuration for the given product name from ../configs.
    Uses configs/config.json to map product_name -> platform_configs/<file>.json
    """
    if not product_name:
        return None

    config_dir = _configs_root()
    mapping_path = os.path.join(config_dir, 'config.json')

    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
    except FileNotFoundError:
        print("config.json not found")
        return None

    if product_name not in mapping:
        print(f"No mapping found for product: {product_name}")
        return None

    config_filename = mapping[product_name]
    platform_config_path = os.path.join(config_dir, 'platform_configs', config_filename)

    try:
        with open(platform_config_path, 'r', encoding='utf-8') as f:
            platform_config = json.load(f)
            return platform_config
    except FileNotFoundError:
        print(f"Platform config file not found: {config_filename}")
        return None

    
def _get_general_regex():
    config_dir = _configs_root()
    regex_path = os.path.join(config_dir, 'main_regex.json')
    try:
        with open(regex_path, 'r', encoding='utf-8') as f:
            regex = json.load(f)
        return regex
    except FileNotFoundError:
        print("config.json not found")
        return None

def _load_platform_regexes(product_name: str):
    """
    Load platform specific regexes for the given product name from ../configs.
    Uses configs/config.json to map product_name -> platform_regexes/<file>.json
    """
    if not product_name:
        return None

    config_dir = _configs_root()
    mapping_path = os.path.join(config_dir, 'config.json')

    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
    except FileNotFoundError:
        print("config.json not found")
        return None

    if product_name not in mapping:
        print(f"No mapping found for product: {product_name}")
        return None

    filename = mapping[product_name]
    platform_regex_path = os.path.join(config_dir, 'platform_regexes', filename)

    try:
        with open(platform_regex_path, 'r', encoding='utf-8') as f:
            platform_regex = json.load(f)
            return platform_regex
    except FileNotFoundError:
        print(f"Platform config file not found: {filename}")
        return None


def _extract_section_blocks(text: str):
    """
    Lightweight pass to split into (title, raw_content) blocks WITHOUT parsing,
    so we can detect product/platform before section-specific parsers run.
    """
    lines = text.splitlines()
    sections = []
    current = {'title': None, 'content': []}

    for line in lines:
        stripped = line.strip()
        if re.fullmatch(r"#+", stripped):
            continue
        if re.match(r"^#+\s*\S.*\S\s*#+$", stripped):
            # push previous
            if current['title'] or current['content']:
                raw_content = '\n'.join(current['content']).rstrip()
                sections.append((current['title'], raw_content))
            # start new
            title = re.sub(r"^#+", "", stripped)
            title = re.sub(r"#+$", "", title).strip()
            current = {'title': title, 'content': []}
        else:
            current['content'].append(line)

    if current['title'] or current['content']:
        raw_content = '\n'.join(current['content']).rstrip()
        sections.append((current['title'], raw_content))

    return sections


def _detect_product_name_from_blocks(blocks):
    """
    Given (title, raw_content) blocks, try to extract a product name
    from either 'fboss2 show product' or 'SMB SERIAL NUMBER' sections.
    """
    # 1) fboss2 show product -> "Product: <name>"
    ans = []
    for title, raw in blocks:
        if title and title.strip().lower() == 'fboss2 show product':
            m = re.search(r'^\s*Product\s*:\s*(.+?)\s*$', raw, flags=re.IGNORECASE | re.MULTILINE)
            if m:
                ans.append(m.group(1).strip())

    # 2) SMB SERIAL NUMBER -> "Product Name: <name>"
    for title, raw in blocks:
        if title and title.strip().upper() == 'SMB SERIAL NUMBER':
            m = re.search(r'^\s*Product\s+Name\s*:\s*(.+?)\s*$', raw, flags=re.IGNORECASE | re.MULTILINE)
            if m:
                ans.append(m.group(1).strip())
    return ans


# ---------------------------
# Public parse flow
# ---------------------------

def parse_sections(text, platform_config=None, regexes=None):
    """
    Parse sections **with** a preloaded platform_config (may be None).
    Platform config is passed down to section parsers in case parsing is platform-sensitive.
    """
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
                parsed_content = parse_content_by_type(section_type, raw_content, platform_config)

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
        parsed_content = parse_content_by_type(section_type, raw_content, platform_config)

        sections.append({
            'title': current['title'],
            'section_type': section_type,
            'parsed_data': parsed_content,
            'raw_content': raw_content,
        })

    # Perform sanity checks with the already loaded platform_config
    sections = perform_sanity_checks(sections, platform_config, regexes)

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

    general_regex = _get_general_regex()
    combined_regexes = general_regex.get('regexes', []) if general_regex else []
 

    # First pass: split into raw blocks to detect product/platform
    blocks = _extract_section_blocks(content)
    product_names = _detect_product_name_from_blocks(blocks)
    platform_config = None
    product_name = None
    for name in product_names:
        curr_config = _load_platform_config(name)
        curr_regex = _load_platform_regexes(name)
        if curr_config:
            product_name = name
            platform_config = curr_config
            combined_regexes += curr_regex.get('regexes', []) if curr_regex else []
            platform_regex = curr_regex if curr_regex else [] 
            break

    # Parse with platform config available up front
    sections = parse_sections(content, platform_config=platform_config, regexes=combined_regexes)

    # Build system map directly from platform_config
    system_map = get_system_map_data(platform_config)

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

    if system_map:
        file_response['system_map'] = system_map

    return [file_response]


# ---------------------------
# ZIP helpers
# ---------------------------

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
