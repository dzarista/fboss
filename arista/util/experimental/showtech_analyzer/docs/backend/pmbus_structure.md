# PMBus Command Data Structure

This document describes the structure and semantics of PMBus commands used in the system. Each command is identified by a unique hexadecimal code and may contain multiple bit fields that represent different functional or configuration flags.

### Data Structure Overview

Each command entry includes:

- **code**: The PMBus command code in hexadecimal format (e.g., `0x00`).
- **name**: The official name of the command.
- **smBusWrite**: The supported SMBus write operation (e.g., `Write Byte`, `Send Byte`, `Write Word`, etc.).
- **smBusRead**: The supported SMBus read operation (e.g., `Read Byte`, `Block Read`, etc.).
- **bytes**: The number of data bytes associated with this command.
- **bitRanges** *(optional)*: A list of bit fields within the data byte(s), where each field includes:
    - **bits**: The bit position(s), e.g., `7:0`, `3`, `15:8`.
    - **name**: A descriptive name for the bit field.
    - **description**: The meaning of the field values and any special behavior.

### Example Command

```json
{
  "code": "0x01",
  "name": "OPERATION",
  "smBusWrite": "Write Byte",
  "smBusRead": "Read Byte",
  "bytes": "1",
  "bitRanges": [
    {
      "bits": "7",
      "name": "Output On/Off",
      "description": "1 = Output ON, 0 = Output OFF"
    },
    {
      "bits": "6",
      "name": "Turn Off Behavior",
      "description": "0 = Turn off immediately, 1 = Use TOFF_DELAY/TOFF_FALL; ignored if bit 7 = 1"
    },
    {
      "bits": "5:4",
      "name": "Voltage Command Source",
      "description": "00 = VOUT_COMMAND, 01 = VOUT_MARGIN_LOW, 10 = VOUT_MARGIN_HIGH, 11 = AVSBus"
    },
    {
      "bits": "3:2",
      "name": "Margin Fault Response",
      "description": "01 = Ignore margin faults, 10 = Act on margin faults, others reserved"
    },
    {
      "bits": "1",
      "name": "Transition Control",
      "description": "1 = Update VOUT_COMMAND with AVSBus before switching, 0 = No update"
    },
    {
      "bits": "0",
      "name": "Reserved",
      "description": "Reserved"
    }
  ]
}

```
### Variable-Length Commands

Some commands use block-level or variable-length communication methods (e.g., `Block Write`, `Block Read Process Call`). For these:

- The `bytes` field is typically set to `"Variable"`.
- `bitRanges` is not supported in this version of the viewer.