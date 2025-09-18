# v1.8.0
- [FEATURE]: Complete database and session management system with MongoDB backend, enabling persistent storage, file uploads, session sharing, and URL-based deep linking to specific sessions. (files and sections automatic opening to be covered).

# v1.7.0
- [FEATURE]: URL fragment navigation added to support linking to specific files and sections. (currently only supports open files in the local cache, will be covered with the DB PR).
- [FEATURE]: Showtech files matching the same product and version have the two features:
  - Can be aligned side by side for easy comparison (this locks the scrolling and only allows per section navigation through the side section filter)
  - Can be diffed to see the differences between the two files. (It is recommended to use it with the Aligned feature simultaneouslty)

# v1.6.1
- [FEATURE]: Added status light on each port in the port table. Green if up, red if down.

# v1.6.0
- [FEATURE]: 
  - Regex detection added to potential anomalies with both general patterns and platform specific ones
  - Detection happens at the upload stage with other anomaly detections.
  - Patterns are detected across a single row or multiple row long patterns of the raw content
  - Rows with matching regexes are highlighted in Red
- [UI]: 
  - ErrorModal includes Regex matches, and on click navigates to the section 
  - Navigation points to the specific row where match occurred.
- [ORGANIZATION]: 
  - Separated ErrorModal CSS to own file
  - Separated logic of Raw Content rendering (to support highlighting Regex anomalies)
  - Created new directory for platform specific regexes. 
  - Renamed files in the configs directory to be more consistent and informative

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

