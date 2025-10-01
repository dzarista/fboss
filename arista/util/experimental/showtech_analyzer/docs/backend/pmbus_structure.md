# I2C Command Specification Structure

This document describes the structure and semantics of I2C command specifications used in the system. These specifications support various I2C devices including PMBus controllers, power management ICs, and other I2C peripherals. Each command is identified by a unique hexadecimal code and may contain multiple bit fields that represent different functional or configuration flags.

### Data Structure Overview

Each command entry includes:

- **code**: The I2C command code in hexadecimal format (e.g., `0x00`).
- **name**: The official name of the command.
- **type**: The access type (e.g., `R/W`, `Read`, `Write`).
- **bytes**: The number of data bytes associated with this command (or `"Variable"`).
- **default_value** *(optional)*: Default value for the command (device-specific).
- **ignore** *(optional)*: Boolean flag to skip parsing this command.
- **bitRanges** *(optional)*: A list of bit fields within the data byte(s), where each field includes:
    - **bits**: The bit position(s), e.g., `7:0`, `3`, `15:8`.
    - **name**: A descriptive name for the bit field.
    - **description**: The meaning of the field values and any special behavior.

### Specification Files

Command specifications are stored in `configs/i2c_specs/` directory:
- **`pmbus_commands.json`** - Standard PMBus commands
- **`isl68226_commands.json`** - Intersil ISL68226 specific commands
- **`ucd90320_commands.json`** - TI UCD90320 specific commands
- **`no_spec_commands.json`** - Fallback for unknown devices

### Example Command

```json
{
  "code": "0x01",
  "name": "OPERATION",
  "type": "R/W",
  "bytes": "1",
  "default_value": "08h",
  "bitRanges": [
    {
      "bits": "7",
      "name": "Enable/Disable Output",
      "description": "0 = Disable, 1 = Enable"
    },
    {
      "bits": "6",
      "name": "Disable Behavior",
      "description": "0 = Immediate off, 1 = Soft off (Use TOFF_DELAY and TOFF_FALL)"
    },
    {
      "bits": "5:4",
      "name": "Vout Source",
      "description": "00 = VOUT_COMMAND, 01 = VOUT_MARGIN_LOW, 10 = VOUT_MARGIN_HIGH, 11 = Not used"
    },
    {
      "bits": "3:2",
      "name": "Margin Response",
      "description": "01 = Ignore Vout OV, UV faults when margined, 10 = Act on Vout OV, UV faults when margined"
    },
    {
      "bits": "1:0",
      "name": "Not Supported",
      "description": "Not supported"
    }
  ]
}
```
### Variable-Length Commands

Some commands use variable-length data. For these:

- The `bytes` field is set to `"Variable"`.
- `bitRanges` is not supported for variable-length commands.
- `ignore` flag can be set to `true` to skip parsing.

### Minimal Commands

For unknown devices, minimal command entries are used:

```json
{
  "code": "0x00",
  "name": "",
  "type": "R/W",
  "bytes": "1"
}
```

These provide basic structure without detailed bit field information.