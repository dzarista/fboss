"""
Log sanity checking module - performs error detection on parsed log data
"""

import re

def detect_critical_sensors(section):
    anomalies = []
    if section.get('section_type') in ('table', 'temperature_table'):
        parsed_data = section.get('parsed_data', {})
        for row_index, row in enumerate(parsed_data.get('rows', [])):
            for key, value in row.items():
                if not value:
                    continue
                value_str = str(value).lower()
                if "critical" in value_str:
                    anomalies.append({
                        'type': 'critical_sensor',
                        'row_index': row_index,
                        'field': key,
                        'value': value,
                        'severity': 'high',
                        'message': f'Critical value detected in {key}: {value}'
                    })
                elif "alarm" in value_str:
                    anomalies.append({
                        'type': 'critical_sensor',
                        'row_index': row_index,
                        'field': key,
                        'value': value,
                        'severity': 'medium',
                        'message': f'Alarm value detected in {key}: {value}'
                    })
    return anomalies

def detect_down_ports(section):
    anomalies = []
    if section.get('section_type') in ('table', 'temperature_table'):
        parsed_data = section.get('parsed_data', {})
        rows = parsed_data.get('rows', [])
        headers = parsed_data.get('headers', [])
        if {'AdminState','LinkState','Transceiver'} <= set(headers):
            for row_index, row in enumerate(rows):
                if (row.get('AdminState') == 'Enabled' and
                    row.get('Transceiver') == 'Present' and
                    row.get('LinkState') == 'Down'):
                    port_name = row.get('Name', f'Port {row_index+1}')
                    anomalies.append({
                        'type': 'port_down',
                        'row_index': row_index,
                        'port_name': port_name,
                        'severity': 'high',
                        'message': f'Port {port_name} is enabled and present but down'
                    })
    return anomalies

def detect_missing_devices(section, platform_config):
    anomalies = []
    if not platform_config or section.get('section_type') != 'lspci':
        return anomalies
    parsed_data = section.get('parsed_data', {})
    found_slots = {d.get('slot') for d in parsed_data.get('devices', []) if d.get('slot')}
    for expected_device in platform_config.get('pcie_devices', []):
        slot = expected_device.get('slot', '')
        if slot and slot not in found_slots:
            anomalies.append({
                'type': 'missing_device',
                'slot': slot,
                'device_type': expected_device.get('device_type','Unknown'),
                'location': expected_device.get('location','Unknown'),
                'description': expected_device.get('description','Unknown'),
                'expected_speed': expected_device.get('expected_speed','Gen1x1'),
                'severity': 'high'
            })
    return anomalies

def parse_pcie_speed_from_lnksta(details):
    if not details:
        return None, None
    m = re.search(r'LnkSta:.*?Speed\s+([0-9.]+)GT/s.*?Width\s+x(\d+)', details, re.I)
    if m:
        return float(m.group(1)), int(m.group(2))
    return None, None

def gen_to_speed_gt(gen_spec):
    if not gen_spec:
        return None, None
    m = re.match(r'Gen(\d+)x(\d+)', gen_spec)
    if not m:
        return None, None
    gen, width = int(m.group(1)), int(m.group(2))
    return {1:2.5, 2:5.0, 3:8.0, 4:16.0, 5:32.0}.get(gen), width

def format_speed_display(speed_gt, width):
    return "Unknown" if speed_gt is None or width is None else f"{speed_gt}GT/s x{width}"

def detect_pcie_speed_mismatches(section, platform_config):
    anomalies = []
    if not platform_config or section.get('section_type') != 'lspci':
        return anomalies
    devices = section.get('parsed_data', {}).get('devices', [])
    found = {d.get('slot'): (d,i) for i,d in enumerate(devices) if d.get('slot')}
    for exp in platform_config.get('pcie_devices', []):
        slot = exp.get('slot','')
        if slot in found:
            device, idx = found[slot]
            actual_gt, actual_w = parse_pcie_speed_from_lnksta(device.get('details',''))
            if actual_gt is not None:
                exp_gt, exp_w = gen_to_speed_gt(exp.get('expected_speed','Gen1x1'))
                if (actual_gt,actual_w) != (exp_gt,exp_w):
                    anomalies.append({
                        'type': 'pcie_speed_mismatch',
                        'slot': slot,
                        'device_type': exp.get('device_type','Unknown'),
                        'location': exp.get('location','Unknown'),
                        'description': exp.get('description','Unknown'),
                        'expected_speed': format_speed_display(exp_gt, exp_w),
                        'actual_speed': format_speed_display(actual_gt, actual_w),
                        'expected_speed_gt': exp_gt,
                        'expected_width': exp_w,
                        'actual_speed_gt': actual_gt,
                        'actual_width': actual_w,
                        'device_index': idx,
                        'severity': 'medium',
                        'message': f"{exp.get('description','Unknown')} at {slot}: Expected {format_speed_display(exp_gt,exp_w)}, found {format_speed_display(actual_gt,actual_w)}"
                    })
    return anomalies

SECTION_ANOMALY_DETECTORS = {
    'fboss2 show environment sensor': [detect_critical_sensors],
    'fboss2 show port': [detect_down_ports],
    'LSPCI': []  # special case
}

def perform_sanity_checks(parsed_sections, platform_config):
    """
    Perform sanity checks with a preloaded platform_config.
    """
    section_map = {s.get('title',''): s for s in parsed_sections}
    for title, funcs in SECTION_ANOMALY_DETECTORS.items():
        if title in section_map:
            section = section_map[title]
            anomalies = []
            if title == 'LSPCI' and platform_config:
                anomalies.extend(detect_missing_devices(section, platform_config))
                anomalies.extend(detect_pcie_speed_mismatches(section, platform_config))
            else:
                for f in funcs:
                    anomalies.extend(f(section))
            if 'parsed_data' in section:
                section['parsed_data']['anomalies'] = anomalies
    return parsed_sections

def get_system_map_data(platform_config):
    """
    Build system_map directly from a preloaded platform_config.
    """
    if platform_config and 'system_map' in platform_config:
        enhanced = dict(platform_config['system_map'])
        enhanced['platform_name'] = platform_config.get('platform','Unknown')
        enhanced['product_name'] = platform_config.get('product_name','Unknown')
        enhanced['description'] = platform_config.get('description','')
        return enhanced
    return None
