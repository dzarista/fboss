""" 
Contains abstract parsers for each section type.
"""

import re
import json
import os
from typing import List
from .section_utils import PMBUS_COMMANDS, extract_bit_field, parse_byte_dump, parse_word_dump

def parse_table(content):
    def parse_cell(cell):
        if cell == "":
            return None
        if re.match(r'^-?\d+(\.\d+)?$', cell):
            return float(cell) if '.' in cell else int(cell)
        return cell

    try:
        lines = content.strip('\n').split('\n')
        clean = [re.sub(r'\x1b\[[0-9;]*m', '', l) for l in lines]

        # locate header (line before a separator of ---)
        header_idx = None
        for i in range(len(clean) - 1):
            if re.match(r'^[-=+\s]*$', clean[i+1]) and len(clean[i+1].strip()) > 2:
                header_idx = i
                break
        if header_idx is None:
            raise ValueError("No table header found")

        raw_header = clean[header_idx]
        separator = clean[header_idx + 1]

        # split headers on two-or-more spaces (allows single spaces within header)
        headers: List[str] = re.split(r'\s{2,}', raw_header.strip())

        # compute start positions for each header
        starts: List[int] = []
        search_pos = 0
        for h in headers:
            pos = raw_header.find(h, search_pos)
            starts.append(pos)
            search_pos = pos + len(h)
        # compute slice bounds
        bounds = [(starts[i], starts[i+1]) for i in range(len(starts)-1)]
        bounds.append((starts[-1], len(raw_header)))

        rows: List[Dict[str, Union[str,int,float,None]]] = []
        for line in clean[header_idx+2:]:
            if not line.strip() or re.match(r'^[-=+\s]*$', line):
                continue

            # If all fields are full, split normally by spacing
            fields = re.split(r'\s{2,}', line.strip())
            if len(fields) == len(headers):
                row = {h: parse_cell(f) for h, f in zip(headers, fields)}
            else:
                # fallback to fixed-column slicing
                row = {}
                for (h, (s, e)) in zip(headers, bounds):
                    cell = line[s:e].strip()
                    row[h] = parse_cell(cell)
            rows.append(row)

        return {
            'type': 'table',
            'headers': headers,
            'rows': rows,
            'row_count': len(rows)
        }

    except Exception:
        return {'type': 'raw', 'data': content}

# Main I2C dump parser
def parse_i2c_dump(content: str):
    lines = content.strip().split('\n')
    byte_lines, word_lines = [], []
    mode = None
    for line in lines:
        if 'i2cdump' in line and ' b' in line:
            mode = 'byte'; continue
        if 'i2cdump' in line and ' w' in line:
            mode = 'word'; continue
        if mode == 'byte':
            byte_lines.append(line)
        elif mode == 'word':
            word_lines.append(line)

    byte_data = parse_byte_dump(byte_lines)
    word_data = parse_word_dump(word_lines)
    has_word = bool(word_data)

    dump = {}
    for addr, info in PMBUS_COMMANDS.items():
        cmd, size, bits = info['name'], info['bytes'], info['bitRanges']
        val = "N/A"  # Default to N/A

        if size == '2':
            if has_word and addr in word_data and word_data[addr] != 'xxxx':
                if word_data[addr].upper() == 'XXXX':
                    val = "N/A"
                else:
                    val = f"0x{word_data[addr]}"
            elif addr in byte_data and byte_data[addr] != 'xx':
                if byte_data[addr].upper() == 'XX':
                    val = "N/A"
                else:
                    val = f"0x{byte_data[addr]} (upper N/A)"
        else:
            if addr in byte_data and byte_data[addr] != 'xx':
                if byte_data[addr].upper() == 'XX':
                    val = "N/A"
                else:
                    val = f"0x{byte_data[addr]}"

        parsed_bits = []
        for br in bits:
            b = br['bits']
            if '(upper N/A)' in val and any(int(x)>=8 for x in (b.split(':') if ':' in b else (b,b))):
                pv, bv = 'N/A','N/A'
            else:
                num = extract_bit_field(val.split('(')[0], b)
                if ':' in b:
                    high, low = map(int, b.split(':'))
                    width = high - low + 1
                else:
                    width = 1
                bv = f"0b{num:0{width}b}" if num is not None else None
                pv = num
            parsed_bits.append({
                'bits': b,
                'name': br['name'],
                'description': br['description'],
                'value': pv,
                'binary_value': bv
            })

        dump[addr] = {
            'value': val,
            'command': cmd,
            'bytes': size,
            'bitRanges': parsed_bits
        }

    return {'type':'i2c_dump','data':dump}

def parse_key_value(content: str):
    try:
        data = {}
        lines = content.strip().split('\n')

        for line in lines:
            line = line.strip()
            if line and ':' in line:
                # Split only on first colon to handle values with colons
                k, v = line.split(':', 1)
                key = k.strip()
                value = v.strip()
                if key:
                    data[key] = value

        if data:
            return {'type':'key_value','data':data}
        else:
            # No key-value pairs found, return as raw
            return {'type':'raw','data':content}

    except Exception as e:
        # If key-value parsing fails, return raw content
        print(f"Key-value parsing failed: {e}")
        return {'type':'raw','data':content}

def parse_lspci(content: str):
    entries = []
    current_entry = {}
    current_lines = []

    for line in content.splitlines():
        if re.match(r"^[0-9a-f]{2}:[0-9a-f]{2}\.\d ", line):  # New device line
            if current_entry:
                current_entry["details"] = '\n'.join(current_lines)
                entries.append(current_entry)
            header = line.strip()
            m = re.match(r"^([0-9a-f:.]+)\s+(.+?):\s+(.+)$", header)
            if m:
                current_entry = {
                    "slot": m.group(1),
                    "class": m.group(2),
                    "description": m.group(3),
                }
            else:
                current_entry = {
                    "slot": "unknown",
                    "class": "unknown",
                    "description": header,
                }
            current_lines = []
        else:
            current_lines.append(line)

    # Append final entry
    if current_entry:
        current_entry["details"] = '\n'.join(current_lines)
        entries.append(current_entry)

    return {
        "type": "lspci",
        "device_count": len(entries),
        "devices": entries,
    }

def parse_fans(content: str):
    """
    Parse fans section with general format:
    Split by commas first, then by colons for key-value pairs.
    Creates dynamic table structure based on found keys.
    """
    try:
        lines = content.strip().split('\n')
        fans = []
        all_keys = set()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for fan indicators (case insensitive, flexible naming)
            fan_match = re.match(r'^(FAN[_\s]*\d+|Fan[_\s]*\d+)', line, re.IGNORECASE)
            if not fan_match:
                continue

            fan_name = fan_match.group(1).strip()

            # Get the rest of the line after fan name
            rest_of_line = line[len(fan_name):].strip()
            if rest_of_line.startswith(':'):
                rest_of_line = rest_of_line[1:].strip()

            # Initialize fan data with the fan name
            fan_data = {'Name': fan_name}

            # Split by commas first to get individual key-value pairs
            comma_parts = [part.strip() for part in rest_of_line.split(',')]

            for part in comma_parts:
                if not part:
                    continue

                # Split by colon to get key-value pairs
                if ':' in part:
                    key_value = part.split(':', 1)
                    if len(key_value) == 2:
                        key = key_value[0].strip()
                        value = key_value[1].strip()

                        # Store the value as-is, including any parentheses content
                        fan_data[key] = value
                        all_keys.add(key)

            # Only add if we found some data beyond just the name
            if len(fan_data) > 1:
                fans.append(fan_data)

        # Create headers list starting with Name, then all other keys found
        headers = ['Name']
        other_keys = sorted([key for key in all_keys if key != 'Name'])
        headers.extend(other_keys)

        # Ensure all fan entries have all keys (fill missing with 'N/A')
        for fan in fans:
            for key in headers:
                if key not in fan:
                    fan[key] = 'N/A'

        return {
            'type': 'fans',
            'headers': headers,
            'rows': fans
        }

    except Exception as e:
        print(f"Fans parsing failed: {e}")
        return {'type': 'raw', 'data': content}

def parse_qsfp_util(content: str):
    """
    Parser using colon-presence to distinguish key:value lines from table rows.
    If a line (trimmed) contains a colon, it's a key/value; otherwise, if it's indented
    deeper than the last header and a current_section is set, it's a table row.
    Lane headers (e.g. 'Lane 1   Lane 2   ...') trigger table mode.
    """
    import re

    try:
        ports = []
        current = {}
        current_section = None
        header_indent = 0
        header_columns = []

        lines = content.strip().splitlines()
        for line in lines:
            # New Port
            if match := re.match(r'^Port (\d+)', line):
                if current:
                    ports.append(current)
                current = {"port": int(match.group(1))}
                current_section = None
                continue

            indent = len(line) - len(line.lstrip(' '))
            stripped = line.strip()

            # Key:Value detection (skip time-like patterns by splitting on first colon)
            if ':' in stripped:
                key, val = stripped.split(':', 1)
                key = key.strip()
                val = val.strip()

                # Table header detection: value is multiple "Lane X" entries
                if re.match(r'^(Lane\s+\d+)(\s+Lane\s+\d+)+$', val):
                    current_section = key
                    header_indent = indent
                    header_columns = re.split(r'\s{2,}', val)
                    current[current_section] = {}
                else:
                    # Regular key/value
                    current[key] = val
                    current_section = None
                continue

            # Table row: no colon, deeper indent than header, and a section active
            if current_section and indent > header_indent:
                parts = stripped.split()
                N = len(header_columns)
                if len(parts) >= N + 1:
                    name = ' '.join(parts[:-N])
                    values = parts[-N:]
                    current[current_section][name] = values

        # Append last port
        if current:
            ports.append(current)

        return {"type": "qsfp_util", "ports": ports}

    except Exception as e:
        print(f"QSFP util parsing failed: {e}")
        return {'type': 'raw', 'data': content}

def parse_fboss2_interface_phy(content: str):
    """
    Parser for `fboss2 show interface phy` output.
    Returns a dict with `type` and list of `interfaces`, each containing:
      - interface: name
      - global properties (Speed, Link State, etc.)
      - sections: {
          'RS FEC': { corrected codewords, uncorrected codewords, Pre-FEC BER, FEC Tail, codeword_stats: [...] },
          'RX PMD': [ {Lane:..., RX Signal Detect Live:..., ...}, ... ],
          'TX PMD': [ {Lane:..., Pre3:..., ...}, ... ]
        }
    """
    import re

    try:
        interfaces = []
        current = None
        current_section = None
        table_mode = None
        table_headers = []

        for line in content.splitlines():
            # Interface start
            m = re.match(r'^\s*Interface\s+(\S+)', line)
            if m:
                if current:
                    interfaces.append(current)
                current = {"interface": m.group(1), "sections": {}}
                current_section = None
                table_mode = None
                continue

            if not current:
                continue

            # Skip separators and blanks
            if re.match(r'^\s*[-=]+\s*$', line) or not line.strip():
                continue
            stripped = line.strip()

            # -- RS FEC section header --
            if re.fullmatch(r'IPHY-Line\s+RS FEC', stripped):
                current_section = 'RS FEC'
                current['sections'][current_section] = {}
                table_mode = None
                continue

            # -- Basic global properties (before any section) --
            if current_section is None:
                kv = re.split(r'\s{2,}', stripped)
                if len(kv) == 2:
                    key, val = kv
                    current[key.strip()] = val.strip()
                continue

            # -- RS FEC key-values before codeword table --
            if current_section == 'RS FEC' and table_mode is None and not stripped.startswith('IPHY-Line Codeword stats'):
                kv = re.split(r'\s{2,}', stripped)
                if len(kv) == 2 and kv[0].startswith('IPHY-Line'):
                    key = kv[0].replace('IPHY-Line ', '').strip()
                    current['sections'][current_section][key] = kv[1].strip()
                continue

            # -- Codeword stats table header --
            if stripped.startswith('IPHY-Line Codeword stats'):
                parts = re.split(r'\s{2,}', stripped)
                # columns are last two parts
                table_headers = parts[-2:]
                current['sections'][current_section]['codeword_stats'] = []
                table_mode = 'codeword'
                continue

            # -- RX PMD table header --
            if stripped.startswith('IPHY-Line RX PMD'):
                parts = re.split(r'\s{2,}', stripped)
                table_headers = parts[1:]
                current_section = 'RX PMD'
                current['sections'][current_section] = []
                table_mode = 'rx_pmd'
                continue

            # -- TX PMD table header --
            if stripped.startswith('IPHY-Line TX PMD'):
                parts = re.split(r'\s{2,}', stripped)
                table_headers = parts[1:]
                current_section = 'TX PMD'
                current['sections'][current_section] = []
                table_mode = 'tx_pmd'
                continue

            # -- Table row parsing --
            if table_mode:
                values = re.split(r'\s+', stripped)
                if len(values) < 1:
                    continue
                row = {}
                for i, h in enumerate(table_headers):
                    row[h] = values[i] if i < len(values) else None
                if table_mode == 'codeword':
                    current['sections']['RS FEC']['codeword_stats'].append(row)
                else:
                    current['sections'][current_section].append(row)
                continue

            # -- Fallback within section for any stray key-values --
            kv = re.split(r'\s{2,}', stripped)
            if len(kv) == 2:
                current['sections'][current_section][kv[0].strip()] = kv[1].strip()

        # Append last interface
        if current:
            interfaces.append(current)

        return {"type": "fboss2_interface_phy", "interfaces": interfaces}

    except Exception as e:
        print(f"FBOSS2 interface phy parsing failed: {e}")
        return {'type': 'raw', 'data': content}

def parse_psu_debug(content: str):
    """
    Parse PSU debug info section with format:
    POWER SUPPLY SLOT 1 DETAILS
    MFR_ID: Arista
    MFR_MODEL: PWR-00591
    ...

    POWER SUPPLY SLOT 2 DETAILS
    MFR_ID: Arista
    ...

    Returns a dict with type 'psu_debug' and list of PSU slots with their properties.
    """
    try:
        lines = content.strip().split('\n')
        psu_slots = []
        current_psu = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for PSU slot header
            slot_match = re.match(r'^POWER SUPPLY SLOT (\d+) DETAILS$', line)
            if slot_match:
                # Save previous PSU if exists
                if current_psu is not None:
                    psu_slots.append(current_psu)

                # Start new PSU
                slot_number = int(slot_match.group(1))
                current_psu = {
                    'slot': slot_number,
                    'properties': {}
                }
                continue

            # Parse key-value pairs for current PSU
            if current_psu is not None and ':' in line:
                # Split only on first colon to handle values with colons
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if key and value:
                    current_psu['properties'][key] = value

        # Add the last PSU if exists
        if current_psu is not None:
            psu_slots.append(current_psu)

        if psu_slots:
            return {
                'type': 'psu_debug',
                'psu_count': len(psu_slots),
                'psu_slots': psu_slots
            }
        else:
            # No PSU data found, return as raw
            return {'type': 'raw', 'data': content}

    except Exception as e:
        print(f"PSU debug parsing failed: {e}")
        return {'type': 'raw', 'data': content}

def parse_content_by_type(ctype: str, content: str):
    if ctype in ('table', 'temperature_table'):
        out = parse_table(content)
        out['type'] = ctype
        return out
    if ctype == 'i2c_dump':
        return parse_i2c_dump(content)
    if ctype == 'key_value':
        return parse_key_value(content)
    if ctype == 'lspci':
        return parse_lspci(content)
    if ctype == 'fans':
        return parse_fans(content)
    if ctype == 'qsfp_util':
        return parse_qsfp_util(content)
    if ctype == 'fboss2_interface_phy':
        return parse_fboss2_interface_phy(content)
    if ctype == 'psu_debug':
        return parse_psu_debug(content)
    if ctype == 'auto_compressed':
        return {
            'type': 'auto_compressed',
            'message': 'This section is compressed by default. Click "Show Raw" to view the full content.',
            'content_size': len(content)
        }
    return {'type':'raw','data':content}