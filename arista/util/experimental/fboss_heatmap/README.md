# FBOSS Heatmap Tool

A web-based visualization tool for analyzing thermal and electrical data from FBOSS systems. Supports both showtech logs and time series CSV data with interactive heatmaps and data export capabilities.

## Features

- **Multiple Data Sources**: Showtech logs and time series CSV files
- **Multiple Data Types**: Temperature, voltage, and fan RPM data
- **Interactive Visualization**: Clickable heatmaps with port details
- **Product Support**: Moranda (4 fans), Quicksilver (4 fans), Whistler (12 fans)
- **Data Export**: CSV generation with configurable time ranges
- **Progress Tracking**: Visual progress bars for file processing
- **Robust Parsing**: Handles various hostname formats and data edge cases

## Quick Start

### Web Interface
1. Open `index.html` in a web browser
2. Select your product type (default: Whistler)
3. Upload a showtech log or time series CSV file
4. View the heatmap and download processed data

### Development Testing
```bash
# Run all tests and validation
make test

# Deploy to web server
make deploy
```

## File Formats

### Showtech Logs
Expected format with transceiver data sections:
```
#### fboss2 show transceiver ####
Port    Status    Temp(C)    Voltage(V)    ...
1       Present   56.0       3.299         ...
```

### Time Series CSV
Expected format:
```
host123.n123.c123.abc1::qsfp_service.qsfp.interface.fab1/1/1.temp,56,"Thu, 08 May 25 00:00:00 -0700",1746687600
host123.n123.c123.abc1::qsfp_service.qsfp.interface.fab1/1/1.vcc.mv,3299.33,"Thu, 08 May 25 00:00:00 -0700",1746687600
host123.n123.c123.abc1::sensor_service.sensor_read.FAN1_RPM.value,5600,"Thu, 08 May 25 00:00:00 -0700",1746687600
```

## Configuration

### Data Types (`data_extraction_config.json`)
- **Temperature**: 0-150°C range, extracted from `.temp` metrics
- **Voltage**: 0-10000mV range, extracted from `.vcc.mv` metrics
- **Fan RPM**: Converted to 0-100% based on 11200 max RPM

### Regex Patterns (`regex_patterns.json`)
- Configurable patterns for metric extraction
- Test cases included for validation
- Supports both `fab1` and `eth1` interface formats

## Testing

### Test Suite (`test_suite.js`)
- Comprehensive extraction testing
- Data validation checks
- Regex pattern verification
- Edge case handling

### Sample Data (`test_data/`)
- Representative CSV samples
- Edge cases and invalid data
- Multiple hostname formats

### Regex Testing (`test_regex_patterns.js`)
- Pattern validation utility
- Test case verification
- Easy pattern debugging

## Development Workflow

1. **Make Changes**: Edit code/configuration
2. **Test**: Run `make test` to verify functionality
3. **Deploy**: Run `make deploy` to update web server
4. **Validate**: Check web interface with real data

## Common Issues

### Temperature Data Shows Zeros
- **Cause**: Regex pattern matching unwanted metrics (e.g., `.temp.high.sum.60`)
- **Fix**: Ensure patterns end with `$` anchor for exact matching

### Large Files Crash Browser
- **Cause**: Memory exhaustion during processing
- **Fix**: Implement streaming/chunked processing for files >10MB

### Missing Data Types
- **Cause**: Independent extraction failure
- **Fix**: Each data type extracted separately, failures isolated

## File Structure

```
fboss_heatmap/
├── index.html                     # Main web interface
├── data_extraction_config.json    # Data type configurations
├── regex_patterns.json           # Regex patterns with tests
├── test_suite.js                 # Comprehensive test suite
├── test_regex_patterns.js        # Regex validation utility
├── test_data/                    # Sample data for testing
│   └── sample_time_series.csv    # Representative test data
├── Makefile                      # Development commands
└── README.md                     # This file
```

## Deployment

The tool is deployed by copying the entire directory to the web server:
```bash
make deploy
# Copies to ~/public_html/llm/fboss_heatmap
```

## Contributing

1. Add test cases for new features in `test_suite.js`
2. Update configuration files for new data types
3. Run `make test` before committing changes
4. Update this README for significant changes

## Troubleshooting

- **Tests failing**: Run `make test` to see detailed error messages
- **Performance issues**: Check file size and consider streaming for large files
- **Data extraction**: Review validation ranges in config files
- **Regex issues**: Check `regex_patterns.json` and test with sample data
