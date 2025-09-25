# Anomaly Detection System

This document explains how the anomaly detection system works in the Showtech Analyzer and how to extend it with new detection capabilities.

## Platform Configuration

> **Adding New Platforms:** For information on adding platform-specific configurations and PCIe device validation, see the [Platform Configuration README](../showtech-backend/configs/README.md).

## Log Sanity Architecture

The anomaly detection system is built around the `log_sanity.py` module, which implements a two-stage architecture:

1. **Parsing Stage**: Files are parsed into structured data by section parsers
2. **Sanity Checking Stage**: The parsed data is analyzed for anomalies and errors

### Core Components

#### `log_sanity.py` Module

The main anomaly detection logic is located in `showtech-backend/utils/log_sanity.py`. This module contains:

- **Detection Functions**: Individual functions that check for specific types of anomalies
- **Section Mapping**: Maps section titles to their corresponding detection functions
- **Platform Integration**: Loads and uses platform configurations for hardware validation

#### Detection Function Structure

Each detection function follows this pattern:

```python
def detect_anomaly_type(section, platform_config=None):
    """Detect specific type of anomaly in a section"""
    anomalies = []

    # Check if this section type is supported
    if section.get('section_type') != 'expected_type':
        return anomalies

    # Extract data from parsed section
    parsed_data = section.get('parsed_data', {})

    # Perform anomaly detection logic
    # ... detection logic here ...

    # Return list of anomaly dictionaries
    return anomalies
```

#### Anomaly Data Structure

Each anomaly should be a dictionary with these fields:

```python
{
    'type': 'anomaly_type_name',           # Unique identifier for anomaly type
    'message': 'Human readable message',    # Description of the issue
    'value': 'problematic_value',          # The actual problematic value (optional)
    'view': 'parsed',                      # View type (parsed/raw)
    'row': 0,                              # For table-based anomalies (optional)
    'slot': 'slot_name',                   # For slot-based anomalies (optional)
    'severity': 'high|medium|low',         # Severity level (optional)
    # ... additional fields specific to anomaly type
}
```

**Note:** Use the `_mk_anomaly()` helper function to create properly formatted anomaly dictionaries.

### Section Anomaly Detectors Map

The `SECTION_ANOMALY_DETECTORS` dictionary maps section titles to their detection functions:

```python
SECTION_ANOMALY_DETECTORS = {
    'fboss2 show environment sensor': [detect_critical_sensors],
    'fboss2 show port': [detect_down_ports],
    'LSPCI': []  # Special case - needs platform config
}
```

### Detection Flow

```
Showtech File → Section Parsing → Product Detection → Platform Config Loading → Anomaly Detection → Error Display
```

1. **Section Parsing**: Each section is parsed into structured data
2. **Product Detection**: Product name extracted from "SMB SERIAL NUMBER" section
3. **Platform Config Loading**: Configuration loaded based on product name in `configs/config.json`
4. **Anomaly Detection**: Each section is checked against its registered detectors
5. **Error Display**: Anomalies are displayed in the frontend

## Current Anomaly Types

### 1. Critical Sensors (`critical_sensor`)
- **Function**: `detect_critical_sensors()`
- **Trigger**: Table cells containing "critical" or "alarm" values
- **Severity**: High (critical), Medium (alarm)
- **Navigation**: Scrolls to specific table row
- **Sections**: Temperature tables, sensor data

### 2. Port Down (`port_down`)
- **Function**: `detect_down_ports()`
- **Trigger**: Ports that are Enabled + Present + Down
- **Navigation**: Scrolls to specific port row
- **Sections**: "fboss2 show port"

### 3. Missing Device (`missing_device`)
- **Function**: `detect_missing_devices()`
- **Trigger**: Expected device not found in LSPCI output
- **Navigation**: Shows expected device information
- **Sections**: "LSPCI" (requires platform config)

### 4. PCIe Speed Mismatch (`pcie_speed_mismatch`)
- **Function**: `detect_pcie_speed_mismatches()`
- **Trigger**: Device running at different speed than expected
- **Navigation**: Scrolls to specific device with red highlighting
- **Sections**: "LSPCI" (requires platform config)

### 5. Regex Matches (`regex_match`)
- **Function**: `detect_regex_matches()`
- **Trigger**: User-defined regex patterns found in raw content
- **Navigation**: Highlights matching text in raw view
- **Sections**: All sections (searches raw content)

## Adding New Anomaly Detection

### Step 1: Create Detection Function

Add a new detection function to `showtech-backend/utils/log_sanity.py`:

```python
def detect_new_anomaly_type(section, platform_config=None):
    """Detect new type of anomaly"""
    anomalies = []

    # Check section type
    if section.get('section_type') != 'target_section_type':
        return anomalies

    parsed_data = section.get('parsed_data', {})

    # Your detection logic here
    # Example: check for specific conditions
    if some_condition:
        anomalies.append(_mk_anomaly(
            type='new_anomaly_type',
            message='Description of the issue',
            row=row_index,  # For table navigation
            value=problematic_value,
            severity='high',  # optional
            # Add other relevant fields as **extra
        ))

    return anomalies
```

### Step 2: Register Detection Function

Add your function to the `SECTION_ANOMALY_DETECTORS` map:

```python
SECTION_ANOMALY_DETECTORS = {
    'Target Section Title': [detect_new_anomaly_type],
    # ... existing mappings
}
```

### Step 3: Frontend Integration

Update frontend components to handle the new anomaly type:

#### ErrorDetection.js
Add cases for your anomaly type in the helper functions:

```javascript
// In getLocationForAnomaly()
case 'new_anomaly_type':
  return `Custom location format`;

// In getValueForAnomaly()
case 'new_anomaly_type':
  return `Custom value format`;

// In getPatternForAnomaly()
case 'new_anomaly_type':
  return `Custom pattern format`;
```

#### ErrorModal.js
Add display name for your error type:

```javascript
// In getErrorTypeDisplay()
case 'new_anomaly_type':
  return 'Human Readable Error Name';
```

### Step 4: Navigation Support

If your anomaly needs custom navigation:

#### For Table-Based Navigation
- Ensure your anomaly includes `row_index`
- The existing navigation will handle scrolling to the row

#### For Custom Navigation
- Add custom navigation logic in `Content.js` `handleNavigateToError()`
- Add unique element IDs in the appropriate renderer
- Implement custom highlighting if needed


## Platform-Specific Detection

Some anomalies require platform configuration data (like PCIe device validation). These functions receive a `platform_config` parameter:

```python
def detect_platform_specific_anomaly(section, platform_config):
    if not platform_config:
        return []  # Skip if no platform config available

    # Use platform_config data for validation
    expected_devices = platform_config.get('pcie_devices', [])
    # ... validation logic
```

### Special Section Handling

The LSPCI section has special handling in the main detection loop:

```python
# Special case for LSPCI - needs platform config
if section_title == 'LSPCI':
    if platform_config:
        missing_device_anomalies = detect_missing_devices(section, platform_config)
        anomalies.extend(missing_device_anomalies)

        speed_mismatch_anomalies = detect_pcie_speed_mismatches(section, platform_config)
        anomalies.extend(speed_mismatch_anomalies)
```

### Custom Data Structures

For complex anomalies, you can include additional data fields:

```python
anomaly = {
    'type': 'complex_anomaly',
    'message': 'Base message',
    'custom_field': 'Additional data',
    'nested_data': {
        'key': 'value'
    }
}
```

Access this data in frontend components through the `anomaly` object passed to helper functions.

## Example: Critical Sensor Detection

Here's how the existing critical sensor detection is implemented, showing the complete flow from backend to frontend:

### Backend Implementation

```python
def detect_critical_sensors(section):
    """Detect critical values in table sections"""
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
```

### Section Registration

```python
# Registered in SECTION_ANOMALY_DETECTORS
SECTION_ANOMALY_DETECTORS = {
    'fboss2 show environment sensor': [detect_critical_sensors],
    # ... other mappings
}
```

### Frontend Integration

```javascript
// ErrorDetection.js - getLocationForAnomaly()
case 'critical_sensor':
  return `Row ${anomaly.row + 1}`;

// ErrorDetection.js - getValueForAnomaly()
case 'critical_sensor':
  return anomaly.value;

// ErrorDetection.js - getPatternForAnomaly()
case 'critical_sensor':
  return anomaly.message || anomaly.pattern || anomaly.type.replace('_', ' ');

// ErrorModal.js - getErrorTypeDisplay()
case 'critical_sensor':
  return 'Critical Sensor';
```

This example demonstrates the complete implementation pattern: detection function, section registration, and frontend integration for displaying and navigating to critical sensor anomalies.
