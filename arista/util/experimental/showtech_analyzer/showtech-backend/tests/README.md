# Testing

Tests covering the core functionality: **parsing**, **sanity checks**, **section parsing**, **file upload**, and **API endpoints**.

## Prerequisites

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Run All Tests
```bash
# Run all tests (recommended)
python -m pytest -v

# or simply 

pytest
```

### 2. Test by Functionality

```bash
# Test Flask API endpoints
python -m pytest tests/test_app.py -v

# Test file upload and parsing
python -m pytest tests/test_file_upload.py -v

# Test sanity checks and anomaly detection
python -m pytest tests/test_log_sanity.py -v

# Test section parsing (tables, key-value)
python -m pytest tests/test_section_parsers.py -v

# Test utility functions
python -m pytest tests/test_section_utils.py -v
python -m pytest tests/test_utils.py -v
```

## Test Directory Structure

### Test Files
- `test_app.py` - **Flask API tests** - Status endpoint, file upload
- `test_file_upload.py` - **File parsing tests** - Section detection, malformed handling
- `test_log_sanity.py` - **Sanity check tests** - Tests anomaly detection functions
- `test_section_parsers.py` - **Section parsing tests** - Tests individual section parsers
- `test_section_utils.py` - **Utility tests** - Type detection, bit field extraction (functions more on the sections helper side)
- `test_utils.py` - **Test helpers** - Helper function utilities

### Test Data
- `test_data/sample_showtech.txt` - Clean showtech (3 sections, no errors)
- `test_data/sample_with_errors.txt` - Showtech with critical sensors (3 sections, errors)
- `test_data/sample_malformed.txt` - Malformed sections (5 sections, graceful handling)
- `test_data/configs/*` - Platform-specific configurations
- `test_data/pmbus_commands.json` - PMBUS command definitions


## Troubleshooting
Make sure venv is activated and you are in the showtech-backend directory when you run these commands.
