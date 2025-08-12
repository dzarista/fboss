# File Processing Pipeline

## Overview

This document outlines the backend architecture of the File Processing Pipeline. The backend is responsible for handling uploaded diagnostic log files, parsing their contents into structured JSON formats, and returning them to the frontend for rendering and analysis.

---

## Pipeline Flow

### Upload Flow Diagram

```
       Upload
         |
     File Handler
	     |
    File Parsing
         |
Section Type Detection
         |
  Specific Parser (or Raw)
         |
   Anomaly Detection
         |
    JSON Output
```

---

## Core Components

### Entry Point

### `/api/upload` (POST Endpoint)

- **Purpose:** Main entrypoint for file uploads from the frontend.
- **Responsibilities:**
    - Accept individual or ZIP file uploads.
    - Call the appropriate file handler based on file type.
    - Return structured JSON containing parsed sections.
---

### Section Processing

### `parse_sections`

- **Purpose:** Core logic for parsing uploaded text into structured sections.
- **Logic:**
    1. Splits the file content line-by-line.
    2. Detects section headers formatted like `### SECTION NAME ###`.
    3. For each section:
        - Extracts raw content.
        - Detects its type using `determine_section_type()`.
        - Compresses raw content using gzip and base64 encoding.
        - Checks if section should be auto-compressed using `should_auto_compress_section()`.
        - For auto-compressed sections: stores metadata instead of parsing.
        - For normal sections: applies the appropriate parser via `parse_content_by_type()`.
    4. Returns a list of structured section objects with compressed raw data.

---

## Section Type Mapping

### `SECTION_TYPES`

Maps section titles to expected parser types:
> Note: I2C don't need to be added to this list as they are detected dynamically.

```json
{
  "fboss2 show port": "table",
  "fboss2 show fabric": "table",
  "fboss show lldp": "table",
  "PCI DEVICES": "lspci",
  ...
}
```

### `determine_section_type`

- **Purpose:** Dynamically determines the appropriate parser type for a section.
- **Logic:**
    1. First checks for exact matches in `SECTION_TYPES` dictionary.
    2. If no exact match, checks if section title contains "i2cdump" (case insensitive).
    3. Falls back to 'raw' type if no matches found.
- **Benefits:**
    - Enables automatic parsing of new i2c dump sections without manual configuration.


## Specialized Parsers

### I2C Dump Parser

- Determines byte or word mode.
- Uses PMBus command info to extract and decode values.
- Handles command matching and bit field extraction.

### Output:

```json
{
  "type": "i2c_dump",
  "data": {
    "0x7d": {
      "value": "0x94",
      "command": "STATUS_TEMPERATURE",
      "bytes": "1",
      "bitRanges": [
        {
          "bits": "7",
          "name": "OT_FAULT",
          "description": "Overtemperature Fault",
          "value": 1,
          "binary_value": "0b1"
        }
      ]
    }
  }
}

```

### Table Parser

- Detects ASCII-style tables and extracts headers and rows.

### Output:

```json
{
  "type": "table",
  "headers": ["Column1", "Column2", "Column3"],
  "rows": [
    {"Column1": "value1", "Column2": "value2", "Column3": "value3"}
  ],
  "row_count": 1
}
```

### Key-Value Parser

- Parses colon-delimited key-value pairs.

### Output:

```json
{
  "type": "key_value",
  "data": {
    "Product": "Arista XYZ123",
    "Serial": "ABC4567890",
    "Uptime": "154h"
  }
}
```

### LSPCI Parser

### `parse_lspci`

- Parses `lspci -vvv` output into device blocks.
- Extracts slot, class, and description headers.
- Gathers detailed multi-line information.

### Output:

```json
{
  "type": "lspci",
  "device_count": 3,
  "devices": [
    {
      "slot": "00:00.0",
      "class": "System peripheral",
      "description": "Intel Corporation Ice Lake Memory Map/VT-d (rev 04)",
      "details": "Subsystem: Intel Corporation Device 0000\nControl: I/O- Mem- BusMaster- ..."
    }
  ]
}
```

---

### Fallback Raw Parser

Used when a section fails parsing or has unknown type.

### Output:

```json
{
  "type": "raw",
  "data": "Unparsed block of text as fallback."
}
```

---

## Anomaly Detection

After parsing, the system performs sanity checks and anomaly detection on the structured data.

### `perform_sanity_checks`

- **Purpose:** Analyzes parsed sections for hardware issues and configuration problems
- **Process:**
    1. **Product Detection**: Extracts product name from "SMB SERIAL NUMBER" section
    2. **Platform Config Loading**: Loads platform-specific configuration based on product name
    3. **Section Analysis**: Runs registered detection functions on relevant sections
    4. **Anomaly Integration**: Adds detected anomalies to section's `parsed_data.anomalies`

### Output Integration

Anomalies are added to each section's parsed data:

```json
{
  "type": "table",
  "headers": ["Sensor", "Value", "Status"],
  "rows": [...],
  "anomalies": [
    {
      "type": "critical_sensor",
      "row_index": 2,
      "field": "Status",
      "value": "Critical",
      "message": "Critical value detected in Status: Critical"
    }
  ]
}
```

> **Detailed Documentation:** See [Anomaly Detection Guide](../anomaly-detection.md) for implementation details and extending the system.

---

## Utility Functions

### **`load_pmbus_commands`**

- Loads command specs from `pmbus_commands.json`.
- Documentation of PMBus commands JSON file can be found in [`docs/backend/pmbus_structure.md`](./pmbus_structure.md)
- Indexed by hex code.

### **`extract_bit_field`**

- Extracts subfield values from hex bytes by bit index.
- Input: value + bit range → Output: numeric + binary form.

### `parse_byte_dump` / `parse_word_dump`

- Parse `i2cdump` outputs to memory-mapped hex tables.

---

### Pipeline Summary

1. **Upload** → File received via `/api/upload`
2. **File Handler** → Single file or ZIP processing
3. **File Parsing** → Content split into sections
4. **Section Type Detection** → Determine parser type
5. **Specific Parser** → Convert to structured data
6. **Anomaly Detection** → Analyze for hardware issues
7. **JSON Output** → Return structured data with anomalies