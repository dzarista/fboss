# Platform Configuration Files

This directory contains platform-specific configuration files used for hardware validation and anomaly detection.

## Quick Start

### Adding a New Platform

1. **Create platform config file** in `Platforms/YourPlatform.json`:
```json
{
  "platform": "YourPlatform",
  "product_name": "YOUR_PRODUCT_CODE", 
  "description": "Platform description",
  "pcie_devices": [
    {
      "slot": "07:00.0",
      "location": "SCM",
      "device_type": "FPGA",
      "description": "SCM FPGA",
      "expected_speed": "Gen1x1"
    }
  ]
}
```

2. **Update `config.json`** to map product name:
```json
{
  "PRODUCT_CODE": "platform.json"
}
```

## File Structure

```
configs/
├── config.json              # Product name → platform file mapping
├── Platforms/               # Platform-specific configurations
│   ├── platform.json       # Platform config file
│   └── ...
└── README.md
```

## Configuration Format

### Platform File Structure
```json
{
  "platform": "Name",
  "product_name": "Product code",
  "description": "Brief description", 
  "pcie_devices": [
    {
      "slot": "PCIe slot (e.g., 07:00.0)",
      "location": "Physical location (SCM/SMB/ASIC0)",
      "device_type": "FPGA/ASIC/etc",
      "description": "Human readable description",
      "expected_speed": "GenXxY (optional, defaults to Gen1x1)"
    }
  ]
}
```

### PCIe Speed Format
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

- **Missing Devices**: Expected devices not found in LSPCI
- **Speed Mismatches**: Devices running at wrong PCIe speeds

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
