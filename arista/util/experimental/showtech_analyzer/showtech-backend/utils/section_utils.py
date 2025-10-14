"""
Contains helper functions for parsing showtech sections.
"""

import re
import json
import os
from typing import List

# Do not add i2c dump sections to this list. They are detected dynamically.
SECTION_TYPES = {
    'fboss2 show environment sensor': 'table',
    'fboss2 show environment temperature': 'temperature_table',
    'fboss2 show environment fan': 'table',
    'fboss2 show environment power': 'table',
    'fboss2 show port': 'table',
    'fboss2 show fabric': 'table',
    'fboss2 show lldp': 'table',
    'fboss2 show interface counters': 'table',
    'fboss2 show interface errors': 'table',
    'fboss2 show interface flaps': 'table',
    'fboss2 show transceiver': 'table',
    'LSPCI': 'lspci',
    'fboss2 show product': 'key_value',
    'FPGA VERSIONS': 'key_value',
    'CFM INFO': 'key_value',
    'PSU DEBUG INFO': 'psu_debug',
    'SMB SERIAL NUMBER': 'key_value',
    'SCM SERIAL NUMBER': 'key_value',
    'FANS': 'fans',
    'wedge_qsfp_util': 'qsfp_util',
    'fboss2 show interface phy': 'fboss2_interface_phy',
}

def determine_section_type(title: str):
    if title in SECTION_TYPES:
        return SECTION_TYPES[title]
    # Check for i2c dump sections (case insensitive)
    if title and 'i2cdump' in title.lower():
        return 'i2c_dump'
    # Default to raw
    return 'raw'

def extract_bit_field(hex_value: str, bit_range: str):
    try:
        value = int(hex_value, 16)
        if ':' in bit_range:
            high, low = map(int, bit_range.split(':'))
        else:
            high = low = int(bit_range)
        mask = (1 << (high - low + 1)) - 1
        return (value >> low) & mask
    except:
        return None

# ---------------- I2C dump helpers ----------------

_HEX_ROW = re.compile(r'^[0-9A-Fa-f]{2}:')  # e.g. "00:"

def _norm_byte_token(tok: str) -> str:
    """Normalize a byte token; return 'xx' for placeholders."""
    t = tok.strip().lower()
    if t in ('--', 'uu', 'xx'):
        return 'xx'
    # keep only 2 hex chars (defensive)
    if re.fullmatch(r'[0-9a-f]{1,2}', t):
        return t.zfill(2)
    return 'xx'

def _norm_word_token(tok: str) -> str:
    """Normalize a word token; return 'xxxx' for placeholders."""
    t = tok.strip().lower()
    if t in ('----', 'xxxx'):
        return 'xxxx'
    # keep only up to 4 hex chars (defensive)
    if re.fullmatch(r'[0-9a-f]{1,4}', t):
        return t.zfill(4)
    return 'xxxx'

def parse_byte_dump(lines: List[str]):
    """
    Parse i2cdump byte mode rows into a dict:
      key: '00'..'ff' (lowercase, no '0x')
      val: '00'..'ff' or 'xx'
    """
    byte_data = {}
    for line in lines:
        if _HEX_ROW.match(line):
            parts = line.strip().split()
            base = int(parts[0].rstrip(':'), 16)
            # take up to 16 byte tokens
            tokens = parts[1:17]
            for i, tok in enumerate(tokens):
                addr_key = f"{(base + i) & 0xFF:02x}"  # 2-digit hex, no 0x
                byte_data[addr_key] = _norm_byte_token(tok)
    return byte_data

def parse_word_dump(lines: List[str]):
    """
    Parse i2cdump word mode rows into a dict:
      key: '00'..'ff' (lowercase, no '0x')
      val: '0000'..'ffff' or 'xxxx'
    """
    word_data = {}
    for line in lines:
        if _HEX_ROW.match(line):
            parts = line.strip().split()
            base = int(parts[0].rstrip(':'), 16)
            # take up to 8 word tokens
            tokens = parts[1:9]
            for i, tok in enumerate(tokens):
                addr_key = f"{(base + i) & 0xFF:02x}"  # 2-digit hex, no 0x
                word_data[addr_key] = _norm_word_token(tok)
    return word_data
