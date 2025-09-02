# v1.5.1
- [BUG]: (v1.5.0 didn't handle case) The i2c parser has been updated to handle STDERR cases (no -b -w was given) and defaults to Byte sized outputs.

# v1.5.0
- [BUG]: The i2c parser has been updated to handle STDERR cases (no -b -w was given) and defaults to Byte sized outputs.
- [STYLE]: Refactored Platform Config detection to the file upload level from the system summary level.

- [FEATURE]: I2C Support
    - Added I2C devices field to Platform Configs
    - Created register map for each of (UCD90320, ISL68226, PMBUS)
    - Each call to `i2cdump` is parsed and matched with a device and register map
    - If the device was not recognized or the register map was not found, do not parse, only `raw`


# v1.4.1
- Extract the hostname and add as Metadata to the JSON output.

- Hostname is displayed in the sidebar and file window navbar.

- In the system summary section these changes were made:
  - Defaulted filtering to temperature (Removed OFF Button)
  - Added Custom gradient button (percentiles). Default gradient is low, high configuration.

- (Minor): Sidebar file tab made as button instead of just file name section

