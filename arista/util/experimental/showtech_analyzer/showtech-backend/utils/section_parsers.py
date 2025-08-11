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
    return {'type':'raw','data':content}