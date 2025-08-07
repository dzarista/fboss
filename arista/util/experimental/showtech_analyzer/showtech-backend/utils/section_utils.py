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

# Load PMBUS commands from JSON
def load_pmbus_commands():
    commands = {}
    json_path = os.path.join(os.path.dirname(__file__), '..', 'pmbus_commands.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
            for item in data:
                command_code = item['code']
                command_name = item['name']
                command_bytes = item.get('bytes', '1')
                commands[command_code.lower()] = {
                    'name': command_name,
                    'bytes': command_bytes,
                    'bitRanges': item.get('bitRanges', [])
                }
    except FileNotFoundError:
        pass
    return commands

PMBUS_COMMANDS = load_pmbus_commands()


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

def parse_byte_dump(lines: List[str]):
    byte_data = {}
    for line in lines:
        if re.match(r'^[0-9A-Fa-f]{2}:', line):
            parts = line.strip().split()
            if len(parts) >= 2:
                base = int(parts[0].rstrip(':'), 16)
                values = parts[1:17]
                for i, val in enumerate(values):
                    addr = f"0x{base+i:02x}"
                    if val and val != '--':
                        byte_data[addr] = val.lower()
                    else:
                        byte_data[addr] = 'xx'
    return byte_data

def parse_word_dump(lines: List[str]):
    word_data = {}
    for line in lines:
        if re.match(r'^[0-9A-Fa-f]{2}:', line):
            parts = line.strip().split()
            if len(parts) >= 2:
                base = int(parts[0].rstrip(':'), 16)
                values = parts[1:9]
                for i, val in enumerate(values):
                    addr = f"0x{base+i:02x}"
                    if val and val != '----':
                        word_data[addr] = val.lower()
                    else:
                        word_data[addr] = 'xxxx'
    return word_data