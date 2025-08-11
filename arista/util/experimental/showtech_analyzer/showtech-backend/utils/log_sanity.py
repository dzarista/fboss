"""
Log sanity checking module - performs error detection on parsed log data
"""

import os
import json
import re

def detect_critical_sensors(section):
    """Detect critical values in table sections"""
    anomalies = []

    if section.get('section_type') in ('table', 'temperature_table'):
        parsed_data = section.get('parsed_data', {})
        rows = parsed_data.get('rows', [])

        if rows:
            for row_index, row in enumerate(rows):
                # Check if any field in the row contains "critical"
                for key, value in row.items():
                    if value and str(value).lower().find('critical') != -1:
                        anomalies.append({
                            'type': 'critical_sensor',
                            'row_index': row_index,
                            'field': key,
                            'value': value,
                            'message': f'Critical value detected in {key}: {value}'
                        })

    return anomalies

def detect_down_ports(section):
    """Detect problematic ports (Enabled + Present + Down)"""
    anomalies = []

    if section.get('section_type') in ('table', 'temperature_table'):
        parsed_data = section.get('parsed_data', {})
        rows = parsed_data.get('rows', [])
        headers = parsed_data.get('headers', [])

        # Check if this is a port table
        if 'AdminState' in headers and 'LinkState' in headers and 'Transceiver' in headers:
            for row_index, row in enumerate(rows):
                admin_state = row.get('AdminState', '')
                link_state = row.get('LinkState', '')
                transceiver = row.get('Transceiver', '')
                port_name = row.get('Name', f'Port {row_index + 1}')

                # Check for problematic ports: Enabled + Present + Down
                if (admin_state == 'Enabled' and
                    transceiver == 'Present' and
                    link_state == 'Down'):
                    anomalies.append({
                        'type': 'port_down',
                        'row_index': row_index,
                        'port_name': port_name,
                        'message': f'Port {port_name} is enabled and present but down'
                    })

    return anomalies

def detect_missing_devices(section, platform_config):
    """Detect missing expected devices in LSPCI section"""
    anomalies = []

    if not platform_config or section.get('section_type') != 'lspci':
        return anomalies

    parsed_data = section.get('parsed_data', {})
    devices = parsed_data.get('devices', [])

    # Get all device slots from LSPCI
    found_slots = set()
    for device in devices:
        slot = device.get('slot', '')
        if slot:
            found_slots.add(slot)

    # Check each expected device from platform config
    expected_devices = platform_config.get('pcie_devices', [])
    for expected_device in expected_devices:
        expected_slot = expected_device.get('slot', '')
        device_type = expected_device.get('device_type', 'Unknown')
        location = expected_device.get('location', 'Unknown')
        description = expected_device.get('description', 'Unknown')
        expected_speed = expected_device.get('expected_speed', 'Gen 1x1')

        if expected_slot and expected_slot not in found_slots:
            anomalies.append({
                'type': 'missing_device',
                'slot': expected_slot,
                'device_type': device_type,
                'location': location,
                'description': description,
                'expected_speed': expected_speed
            })

    return anomalies

def parse_pcie_speed_from_lnksta(details):
    """Parse PCIe speed and width from LnkSta line in LSPCI details"""
    if not details:
        return None, None

    # Look for LnkSta line with speed and width information
    # Example: "LnkSta:	Speed 2.5GT/s (ok), Width x1 (ok)"
    lnksta_match = re.search(r'LnkSta:.*?Speed\s+([0-9.]+)GT/s.*?Width\s+x(\d+)', details, re.IGNORECASE)
    if lnksta_match:
        speed_gt = float(lnksta_match.group(1))
        width = int(lnksta_match.group(2))
        return speed_gt, width

    return None, None

def gen_to_speed_gt(gen_spec):
    """Convert generation format (e.g., 'Gen1x1') to GT/s speed and width"""
    if not gen_spec:
        return None, None

    # Parse format like "Gen1x1", "Gen4x4"
    import re
    match = re.match(r'Gen(\d+)x(\d+)', gen_spec)
    if not match:
        return None, None

    gen = int(match.group(1))
    width = int(match.group(2))

    # Map generations to GT/s speeds
    speed_map = {
        1: 2.5,
        2: 5.0,
        3: 8.0,
        4: 16.0,
        5: 32.0
    }

    speed_gt = speed_map.get(gen)
    return speed_gt, width

def format_speed_display(speed_gt, width):
    """Format speed and width for display"""
    if speed_gt is None or width is None:
        return "Unknown"
    return f"{speed_gt}GT/s x{width}"

def detect_pcie_speed_mismatches(section, platform_config):
    """Detect PCIe speed mismatches in LSPCI section"""
    anomalies = []

    if not platform_config or section.get('section_type') != 'lspci':
        return anomalies

    parsed_data = section.get('parsed_data', {})
    devices = parsed_data.get('devices', [])

    # Create a map of found devices by slot with their indices
    found_devices = {}
    for device_index, device in enumerate(devices):
        slot = device.get('slot', '')
        if slot:
            found_devices[slot] = {'device': device, 'index': device_index}

    # Check each expected device from platform config
    expected_devices = platform_config.get('pcie_devices', [])
    for expected_device in expected_devices:
        expected_slot = expected_device.get('slot', '')
        device_type = expected_device.get('device_type', 'Unknown')
        location = expected_device.get('location', 'Unknown')
        description = expected_device.get('description', 'Unknown')
        # Default to Gen1x1 if no expected_speed is specified
        expected_speed = expected_device.get('expected_speed', 'Gen1x1')

        if expected_slot in found_devices:
            device_info = found_devices[expected_slot]
            device = device_info['device']
            device_index = device_info['index']
            details = device.get('details', '')

            # Parse actual speed from device details
            actual_speed_gt, actual_width = parse_pcie_speed_from_lnksta(details)
            if actual_speed_gt is not None and actual_width is not None:
                # Convert expected speed from generation format to GT/s
                expected_speed_gt, expected_width = gen_to_speed_gt(expected_speed)

                # Compare actual vs expected speeds
                if (actual_speed_gt != expected_speed_gt or actual_width != expected_width):
                    expected_display = format_speed_display(expected_speed_gt, expected_width)
                    actual_display = format_speed_display(actual_speed_gt, actual_width)

                    anomalies.append({
                        'type': 'pcie_speed_mismatch',
                        'slot': expected_slot,
                        'device_type': device_type,
                        'location': location,
                        'description': description,
                        'expected_speed': expected_display,
                        'actual_speed': actual_display,
                        'expected_speed_gt': expected_speed_gt,
                        'expected_width': expected_width,
                        'actual_speed_gt': actual_speed_gt,
                        'actual_width': actual_width,
                        'device_index': device_index,  # Add device index for navigation
                        'message': f'{description} at {expected_slot}: Expected {expected_display}, found {actual_display}'
                    })

    return anomalies

def load_platform_config(product_name):
    """Load platform configuration for the given product name"""
    if not product_name:
        return None

    config_dir = os.path.join(os.path.dirname(__file__), '..', 'configs')
    mapping_path = os.path.join(config_dir, 'config.json')

    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)

        if product_name in mapping:
            config_filename = mapping[product_name]
            platform_config_path = os.path.join(config_dir, 'Platforms', config_filename)

            try:
                with open(platform_config_path, 'r', encoding='utf-8') as f:
                    platform_config = json.load(f)
                    # print(f"Platform config for {product_name}:")
                    # print(json.dumps(platform_config, indent=2))
                    return platform_config
            except FileNotFoundError:
                print(f"Platform config file not found: {config_filename}")
        else:
            print(f"No mapping found for product: {product_name}")
    except FileNotFoundError:
        print("config.json not found")

    return None

# Map section titles to their specific anomaly detection functions
SECTION_ANOMALY_DETECTORS = {
    'fboss2 show environment sensor': [detect_critical_sensors],
    'fboss2 show port': [detect_down_ports],
    'LSPCI': []  # Special case - needs platform config
}

def perform_sanity_checks(parsed_sections):
    """
    Perform sanity checks only on sections that need them
    Returns the sections with anomalies added to their parsed_data
    """
    
    # Create a lookup map for faster section access
    section_map = {section.get('title', ''): section for section in parsed_sections}
    product_name = None

    platform_config = None

    # First, extract product name from fboss2 show product section
    if 'fboss2 show product' in section_map:
        section = section_map['fboss2 show product']
        parsed_data = section.get('parsed_data', {})
        if parsed_data.get('type') == 'key_value':
            product_data = parsed_data.get('data', {})
            product_name = product_data.get('Product', '').strip()

            # Load platform configuration if product name exists
            platform_config = load_platform_config(product_name)

    if not platform_config and 'SMB SERIAL NUMBER' in section_map:
        section = section_map['SMB SERIAL NUMBER']
        parsed_data = section.get('parsed_data', {})
        if parsed_data.get('type') == 'key_value':
            product_data = parsed_data.get('data', {})
            product_name = product_data.get('Product Name', '').strip()

            # Load platform configuration if product name exists
            platform_config = load_platform_config(product_name)

    # Now perform anomaly detection only on sections that need it
    for section_title, detector_funcs in SECTION_ANOMALY_DETECTORS.items():
        if section_title in section_map:
            section = section_map[section_title]
            anomalies = []

            # Special case for LSPCI - needs platform config
            if section_title == 'LSPCI':
                if platform_config:
                    # Check for missing devices
                    missing_device_anomalies = detect_missing_devices(section, platform_config)
                    anomalies.extend(missing_device_anomalies)

                    # Check for PCIe speed mismatches
                    speed_mismatch_anomalies = detect_pcie_speed_mismatches(section, platform_config)
                    anomalies.extend(speed_mismatch_anomalies)
            else:
                # Run the standard detection functions for this section
                for detector_func in detector_funcs:
                    section_anomalies = detector_func(section)
                    anomalies.extend(section_anomalies)

            # Add anomalies to the section's parsed_data
            if 'parsed_data' in section:
                section['parsed_data']['anomalies'] = anomalies

    return parsed_sections