"""
Log sanity checking module - performs error detection on parsed log data
"""

import re

def _mk_anomaly(*, type, message, value=None, view='parsed', row=None, slot=None,
                severity=None, **extra):
    a = {'type': type, 'message': message, 'value': value, 'view': view}
    if row is not None:
        a['row'] = int(row)
    if slot:
        a['slot'] = str(slot)
    if severity:
        a['severity'] = severity
    # keep optional extras (device_index, speeds, etc.) if provided
    for k, v in extra.items():
        if v is not None:
            a[k] = v
    return a

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
                    anomalies.append(_mk_anomaly(
                        type='critical_sensor',
                        row=row_index,
                        value=value,
                        message=f'Critical value detected in {key}: {value}',
                        view='parsed',
                        severity='high'
                    ))
                elif "alarm" in value_str:
                    anomalies.append(_mk_anomaly(
                        type='critical_sensor',
                        row=row_index,
                        value=value,
                        message=f'Alarm value detected in {key}: {value}',
                        view='parsed',
                        severity='medium'
                    ))
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
                    anomalies.append(_mk_anomaly(
                        type='port_down',
                        row=row_index,
                        value=port_name,
                        message=f'Port {port_name} is enabled and present but down',
                        view='parsed',
                        severity='high'
                    ))
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
            desc = expected_device.get('description', 'Unknown')
            anomalies.append(_mk_anomaly(
                type='PCIe Device Missing',
                message=f'Missing Device ({desc}) on {slot}',
                value=desc,
                view='parsed',
                slot=slot,
                severity='high',
                device_type=expected_device.get('device_type', 'Unknown'),
                location=expected_device.get('location', 'Unknown'),
                expected_speed=expected_device.get('expected_speed', 'Gen1x1'),
            ))
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
    """
    Emit anomalies in the same shape as 'PCIe Device Missing'.
    Only read the observed (seen) speed from the section; all other fields
    come from platform_config.
    """
    anomalies = []
    if not platform_config or section.get('section_type') != 'lspci':
        return anomalies

    devices = section.get('parsed_data', {}).get('devices', [])
    # slot -> (device, index)
    found = {d.get('slot'): (d, i) for i, d in enumerate(devices) if d.get('slot')}

    for exp in platform_config.get('pcie_devices', []):
        slot = exp.get('slot', '')
        if not slot or slot not in found:
            continue

        device, idx = found[slot]

        # Parse only the SEEN speed from the actual section
        actual_gt, actual_w = parse_pcie_speed_from_lnksta(device.get('details', ''))
        if actual_gt is None or actual_w is None:
            continue  # can't evaluate

        # Expected comes from platform config (raw GenNxW string)
        expected_spec = exp.get('expected_speed', 'Gen1x1')
        exp_gt, exp_w = gen_to_speed_gt(expected_spec)

        # If it mismatches, emit unified anomaly
        if (exp_gt, exp_w) != (actual_gt, actual_w):
            desc = exp.get('description', 'Unknown')
            anomalies.append(_mk_anomaly(
                type='PCIe Device Speed Mismatch',
                message=f"Speed mismatch for {desc} on {slot}: expected {format_speed_display(exp_gt, exp_w)}, "
                        f"observed {format_speed_display(actual_gt, actual_w)}",
                value=desc,
                view='parsed',
                slot=slot,
                severity='medium',
                device_index=idx,  # <-- added
                device_type=exp.get('device_type', 'Unknown'),
                location=exp.get('location', 'Unknown'),
                expected_speed=expected_spec,  # keep raw GenNxW like the 'Missing' anomaly
                actual_speed=format_speed_display(actual_gt, actual_w),  # only field taken from section
            ))
    return anomalies



SECTION_ANOMALY_DETECTORS = {
    'fboss2 show environment sensor': [detect_critical_sensors],
    'fboss2 show port': [detect_down_ports],
    'LSPCI': []  # special case
}


def detect_regex_matches(section, regexes):
    anomalies = []
    raw_content = section.get('raw_content', '')

    if not raw_content or not regexes:
        return anomalies

    # Step 1: Detect regexes on the entire raw content
    for regex in regexes:
        name, patterns = regex.get("name"), regex.get("patterns")
        if not patterns:
            continue
        for pattern in patterns:
            if not pattern:
                continue
            try:
                for match in re.finditer(pattern, raw_content, re.MULTILINE | re.DOTALL):
                    match_start = match.start()
                    match_end = match.end()

                    # Step 2: Find which line the match starts on (for navigation)
                    start_line = raw_content[:match_start].count('\n')

                    # Step 3: Create line-by-line spans for highlighting
                    match_text = match.group(0)
                    lines_in_match = match_text.split('\n')
                    line_spans = []

                    # Calculate the position of the start of the starting line
                    line_start_pos = raw_content.rfind('\n', 0, match_start) + 1

                    # Create spans for each line that contains part of the match
                    for i, line_text in enumerate(lines_in_match):
                        current_line = start_line + i

                        # Calculate span within this line
                        if i == 0:
                            # First line: span starts at match position within the line
                            span_start = match_start - line_start_pos
                            span_end = span_start + len(line_text)
                        else:
                            # Subsequent lines: span starts at beginning of line
                            span_start = 0
                            span_end = len(line_text)

                        line_spans.append({
                            'line': current_line,
                            'span': [span_start, span_end]
                        })

                        # Update line_start_pos for next iteration
                        if i < len(lines_in_match) - 1:  # Not the last line
                            line_start_pos += len(line_text) + 1  # +1 for the newline

                    # Create one anomaly per match with uppermost line for navigation
                    # and all line spans for highlighting
                    first_line_start_pos = raw_content.rfind('\n', 0, match_start) + 1
                    anomalies.append(_mk_anomaly(
                        type='Regex Match',
                        value=name,
                        message=f"Pattern '{pattern}' matched: '{match.group(0)[:100]}{'...' if len(match.group(0)) > 100 else ''}'",
                        view='raw',
                        field=name,
                        line=start_line,  # Navigation goes to the first line
                        span=[match_start - first_line_start_pos, match_end - first_line_start_pos] if len(lines_in_match) == 1 else None,
                        line_spans=line_spans  # All spans for highlighting
                    ))

            except re.error as e:
                print(f"Warning: Skipping invalid regex pattern '{pattern}': {e}")

    return anomalies



def perform_sanity_checks(parsed_sections, platform_config, regexes):
    for section in parsed_sections:
        anomalies = []

        if regexes:
            anomalies.extend(detect_regex_matches(section, regexes))

        title = section.get('title', '')
        if title in SECTION_ANOMALY_DETECTORS:
            if title == 'LSPCI' and platform_config:
                anomalies.extend(detect_missing_devices(section, platform_config))
                anomalies.extend(detect_pcie_speed_mismatches(section, platform_config))
            else:
                for detector_func in SECTION_ANOMALY_DETECTORS[title]:
                    anomalies.extend(detector_func(section))

        if anomalies:
            section['anomalies'] = anomalies
            if 'parsed_data' not in section:
                section['parsed_data'] = {}

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
