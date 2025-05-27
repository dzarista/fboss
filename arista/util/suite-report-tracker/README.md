# Ship Report Spreadsheet Tracker Tool

This tool generates FBOSS ship reports and updates [FBOSS Ship Report](https://docs.google.com/spreadsheets/d/1rxbJpzKbnVXoMFdHTLBD-GX1pi-NZGJA5LROdPwJ054/edit) spreadsheet.

## Usage

This tool is made to run on home-bus. To use this tool, create a new container or use an existing one. 

To simply update [FBOSS Ship Report](https://docs.google.com/spreadsheets/d/1rxbJpzKbnVXoMFdHTLBD-GX1pi-NZGJA5LROdPwJ054/edit) spreadsheet with default settings:
```
python3 UpdateFbossReportSpreadsheet.py CONTAINER_HOSTNAME
```

### To use your own spreadsheet:
  1. Create a spreadsheet with new worksheets, and make the
     spreadsheet world writeable.

  2. Create a suite report worksheet with the following columns
        
        Suite, Full Name, Runs, Passes, Fails, Pass%, Residual Pass%, Coverage

  3. Create a test run worksheet with the following columns 
  
        Test Name, Pass%, Runs, Passes, Fails, Timeouts

  4. Create a pass rate worksheet with the following columns
        
        Date, -21d, -14d, -7d, 0d

  5. Run the tool providing your spreadsheet ID and worksheet names

### Full Usage
```
usage: UpdateFbossReportSpreadsheet.py [-h] [-s SPREADSHEET] [-w WORKSHEETS WORKSHEETS WORKSHEETS] [-p PROJECT] HOST

positional arguments:
  HOST                  full container hostname

optional arguments:
  -h, --help            show this help message and exit
  -s SPREADSHEET, --spreadsheet SPREADSHEET
                        Key to Google spreadsheet in
                        https://docs.google.com/spreadsheets/d/<key>/edit
  -w WORKSHEETS WORKSHEETS WORKSHEETS, --worksheets WORKSHEETS WORKSHEETS WORKSHEETS
                        Name of worksheets within spreadsheet to store data to.
  -p PROJECT, --project PROJECT
                        Project name. Default: fboss_schedule_autotest
```