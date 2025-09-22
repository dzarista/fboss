# Ship Report Spreadsheet Tracker Tool

This tool generates FBOSS ship reports and updates [FBOSS Ship Report](https://docs.google.com/spreadsheets/d/1rxbJpzKbnVXoMFdHTLBD-GX1pi-NZGJA5LROdPwJ054/edit) spreadsheet.

## Usage

This tool is made to run on home-bus. To use this tool, create a new fboss container 

To simply update [FBOSS Ship Report](http://go/fboss-shipreport) spreadsheet with default settings:
1. Copy `generate_reports_container.sh` into your CONTAINER at:
      ```
      /user/suite-report-tracker/generate_fboss_suite_reports.sh
      ```
   ensure the script has executable permission `chmod +x <script>`

2. Run `UpdateFbossReportSpreadsheet.py` to generate suite reports and update tracker spreadsheet
      ```
      python3 UpdateFbossReportSpreadsheet.py CONTAINER_NAME CONTAINER_HOSTNAME
      ```
      Optional: this can be run as a cron job in homebus

### Adding a new platform
1. Add the commands to generate suite report for new TestSuite in `generate_reports_container.sh`
2. Copy the updated `generate_reports_container.sh` to your container
3. Add the new TestSuite name to `suite` list in `UpdateFbossReportSpreadsheet.py`
4. Run `UpdateFbossReportSpreadsheet.py` as above to verify
5. The cronjob for this tool is currently managed by @huyc

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