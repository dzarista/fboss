# Configuration Files

This directory contains configuration files for hardware validation, anomaly detection, I2C device specifications, and regex pattern matching.

## Adding a New Platform

1. **Create platform config file** in `platform_configs/NewPlatform.json`:
```json
{
  "platform": "NewPlatform",
  "product_name": "NEW_PRODUCT_CODE",
  "description": "Platform description",
  "pcie_devices": [...],
  "i2c_devices": {...},
  "system_map": {...}
}
```

2. **Create platform regex file** in `platform_regexes/NewPlatform.json`:
```json
{
  "platform": "NewPlatform",
  "product_name": "NEW_PRODUCT_CODE",
  "description": "Platform-specific regex patterns",
  "regexes": [
    {
      "name": "Pattern Name",
      "patterns": ["regex1", "regex2"]
    }
  ]
}
```

3. **Update `config.json`** to map product name:
```json
{
  "NEW_PRODUCT_CODE": "NewPlatform.json"
}
```

## File Structure

```
configs/
├── config.json              # Product name → platform file mapping
├── main_regex.json          # Global regex patterns for all platforms
├── platform_configs/        # Platform-specific hardware configurations
│   ├── Viper.json          # Viper platform config
│   ├── Whistler.json       # Whistler platform config
│   └── QuicksilverPFb.json  # Quicksilver platform config
├── platform_regexes/        # Platform-specific regex patterns
│   ├── Viper.json          # Viper regex patterns
│   ├── Whistler.json       # Whistler regex patterns
│   └── QuicksilverPFb.json  # Quicksilver regex patterns
├── i2c_specs/               # I2C device command specifications
│   ├── pmbus_commands.json  # Standard PMBus commands
│   ├── isl68226_commands.json # Intersil ISL68226 commands
│   ├── ucd90320_commands.json # TI UCD90320 commands
│   └── no_spec_commands.json  # Fallback for unknown devices
└── README.md
```

## Configuration Format

### Platform Config Structure (`platform_configs/`)
```json
{
  "platform": "Name",
  "product_name": "Product code",
  "description": "Brief description",
  "pcie_devices": [...],
  "i2c_devices": {...},
  "system_map": {...}
}
```

### Platform Regex Structure (`platform_regexes/`)
```json
{
  "platform": "Name",
  "product_name": "Product code",
  "description": "Platform-specific regex patterns",
  "regexes": [
    {
      "name": "Pattern description",
      "patterns": ["regex1", "regex2"]
    }
  ]
}
```

### Global Regex Structure (`main_regex.json`)
```json
{
  "description": "Global regex patterns for all platforms",
  "regexes": [
    {
      "name": "Pattern category name",
      "patterns": ["regex_1", "regex_2"]
    }
  ]
}
```

### I2C Device Specifications (`i2c_specs/`)
```json
[
  {
    "code": "0x00",
    "name": "COMMAND_NAME",
    "type": "R/W",
    "bytes": "1",
    "bitRanges": [...]
  }
]
```

## Regex Pattern System

### Global Patterns (`main_regex.json`)
- Contains regex patterns that apply to all platforms
- Used for general anomaly detection across all devices
- Patterns here are checked against all showtech files regardless of platform

### Platform-Specific Patterns (`platform_regexes/`)
- Contains regex patterns specific to each platform
- Used for platform-specific anomaly detection

### Pattern Structure
```json
{
  "name": "Descriptive name for the pattern",
  "patterns": ["regex_pattern_1", "regex_pattern_2"]
}
```

## PCIe Speed Format
- `Gen1x1` = 2.5GT/s x1 (default for FPGAs)
- `Gen4x4` = 16.0GT/s x4 (typical for ASICs)

## Current Platforms

| Platform | Product Codes | Devices |
|----------|---------------|---------|
| **Viper** | MERU800BIA, MERU800BIAB | SCM FPGA, SMB FPGA, ASIC0 |
| **Whistler** | MERU800BFA | SCM FPGA, 4x SMB FPGAs, 2x ASICs |
| **Quicksilver** | GLATH05a-64o | SCM FPGA, SMB FPGA, ASIC0 |

## Anomaly Detection

The system automatically detects:

- **Missing PCIe Devices**: Expected devices not found in LSPCI
- **PCIe Speed Mismatches**: Devices running at wrong speeds
- **Critical Sensors**: Temperature/voltage sensors in critical state
- **Regex Matches**: Custom patterns found in raw content
- **I2C Communication Issues**: Failed I2C device communications

## Validation Process

1. **Product Detection**: Extract product name from showtech "SMB SERIAL NUMBER" section
2. **Config Loading**: Load platform config based on product name mapping
3. **LSPCI Analysis**: Compare actual vs expected PCIe devices and speeds
4. **Error Display**: Show anomalies in error modal with navigation

## Troubleshooting

### Config Not Loading
- Check product name in showtech matches `config.json` exactly
- Verify JSON syntax is valid
- Ensure file permissions allow reading
