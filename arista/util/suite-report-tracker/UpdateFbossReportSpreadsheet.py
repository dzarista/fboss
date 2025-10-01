import sys
import argparse
import textwrap as _textwrap
import json
import subprocess
import SpreadsheetLibV5
import pytz
from datetime import datetime, timedelta
from SuiteReport import SuiteReport

limits = ['7d', '14d', '21d', '28d']
suites = [
   ["FbossOssViperShip"],
   ["FbossOssViperBShip"],
   ["FbossOssWhistlerShip"],
   ["FbossRackhawkShip"],
   ["FbossRackhawkShip", "rkdo"],
   ["FbossOssShip", "qsfb"],
]

def split_by_indices(text, indices):
   if not indices:
      return [text]

   indices = sorted(list(set(indices)))
   splits = []
   last_split = 0
   for index in indices:
      splits.append(text[last_split:index])
      last_split = index
   splits.append(text[last_split:])
   return [s.strip() for s in splits if s]

# Get latest build info from
#   a build ls -p <project> -m 1
def get_latest_build_info(project):
   print(f"--- Getting latest build info for {project} ---")
   command = ["a", "build", "ls", "-p", project, "-m" "1"]
   result = subprocess.run(command, capture_output=True, check=True)
   stdout_string = result.stdout.decode('utf-8')
   lines = stdout_string.split("\n")

   split_indices = [i for i, char in enumerate(lines[1]) if char == " "]
   keys = split_by_indices(lines[0], split_indices)
   vals = split_by_indices(lines[2], split_indices)

   return {k: v for k, v in zip(keys, vals)}

# Generate ship report json and csv with
#   generate_fboss_suite_reports.sh
def generate_suite_reports(container, host, project):
   print(f"--- Generating suite reports on {host} ---")
   script_path = "./generate_fboss_suite_reports.sh"
   try:
      command = [script_path, container, host, project]
      subprocess.run(command, check=True)
      print("Sucessfully generated suite reports")
   except subprocess.CalledProcessError as e:
      print(f"Error: error while generating suite reports: {e}", file=sys.stderr)
      sys.exit(1)
   except FileNotFoundError:
      print(f"Error: Script not found at {script_path}", file=sys.stderr)
      sys.exit(1)


# Update the "fboss ship reports (7d)" worksheet
# Sheet Column Format:
#   Suite, Full Name, Runs, Passes, Fails, Pass%, Residual Pass%, Coverage
def update_7d_suite_report_sheet(sheet, suite_reports_7d, build_info):
   sheet.setKeyCol("Suite")

   for suite_rp_7d in suite_reports_7d:
      sheet_row = sheet.getRow(suite_rp_7d.custom_name)
      if not sheet_row:
         sheet_row = sheet.addRow(suite_rp_7d.custom_name)

      sheet_row.set("Full Name", suite_rp_7d.fullname)
      sheet_row.set("Runs", int(suite_rp_7d.runs))
      sheet_row.set("Passes", int(suite_rp_7d.passed))
      sheet_row.set("Fails", int(suite_rp_7d.failed))
      sheet_row.set("Pass%", float(suite_rp_7d.pass_rate) / 100)
      sheet_row.set("Residual Pass%", float(suite_rp_7d.residual_pass_rate) / 100)
      sheet_row.set("Coverage", float(suite_rp_7d.coverage) / 100)

   # set Build Info row (last row)
   sheet_row = sheet.getRow("Lastest Build")
   build_info_str = "build id: {}\nproject: {}\nstart time: {}\nduration: {}" \
                    "\nresult: {}".format(build_info['id'],
                                          build_info['project'],
                                          build_info['start time'],
                                          build_info['duration'],
                                          build_info['result'])
   sheet_row.set("Full Name", build_info_str)

   sheet.commitChanges()
   sheet.sort("Pass%", ascending=False, endRowOffset=-2)
   print(f"Succesfully updated \"{sheet.name()}\" sheet")


# Update the "fboss ship test runs (7d)" worksheet
# Sheet Column Format:
#   Test Name, Pass%, Runs, Passes, Fails, Timeouts
def update_7d_test_run_sheet(sheet, suite_reports_7d):
   sheet.setKeyCol("Test Name")
   all_rows = sheet.getRows()

   # set Last Updated row (second row)
   now_pst = datetime.now(pytz.timezone('US/Pacific'))
   formatted_now = now_pst.strftime('%Y-%m-%d %H:%M:%S %Z%z')
   last_updated_str = f"Last updated: {formatted_now}"
   if all_rows:
      last_updated_row = all_rows[0]
      last_updated_row.set("Test Name", last_updated_str)
   else:
      last_updated_row = sheet.addRow(last_updated_str)

   # clear test run rows
   for row in all_rows[1:]:
      sheet.deleteRow(row)

   sheet.commitChanges()

   for suite_rp in suite_reports_7d:
      sheet.addRow(f"{suite_rp.custom_name} Test Runs (7d)")
      for test_run in suite_rp.test_runs:
         row_key = f"{suite_rp.custom_name}::{test_run.test_name}"

         sheet_row = sheet.addRow(row_key)
         sheet_row.set("Pass%", test_run.pass_rate)
         sheet_row.set("Runs", test_run.runs)
         sheet_row.set("Passes", test_run.passes)
         sheet_row.set("Fails", test_run.fails)
         sheet_row.set("Timeouts", test_run.timeouts)

   sheet.commitChanges()
   print(f"Succesfully updated \"{sheet.name()}\" sheet")


# Update the "fboss ship pass rate history" worksheet
# Sheet Column Format:
#   Date, -28d, -21d, -14d, 0d
def update_pass_rate_history_sheet(sheet, suite_reports_all):
   sheet.setKeyCol("Date")
   suite_reports_7d = suite_reports_all[0]
   suite_reports_14d = suite_reports_all[1]
   suite_reports_21d = suite_reports_all[2]
   suite_reports_28d = suite_reports_all[3]

   now_pst = datetime.now(pytz.timezone('US/Pacific'))
   today_pst = now_pst.date()

   sheet_row = sheet.getRow("Suite")
   if not sheet_row:
      sheet_row = sheet.addRow("Suite")
   sheet_row.set("0d", today_pst)
   sheet_row.set("-7d", (today_pst - timedelta(weeks=1)))
   sheet_row.set("-14d", (today_pst - timedelta(weeks=2)))
   sheet_row.set("-21d", (today_pst - timedelta(weeks=3)))
   sheet.commitChanges()

   for i, suite_rp in enumerate(suite_reports_7d):
      sheet_row = sheet.getRow(suite_rp.custom_name)
      if not sheet_row:
         sheet_row = sheet.addRow(suite_rp.custom_name)

      sheet_row.set("0d", float(suite_rp.pass_rate) / 100)
      sheet_row.set("-7d", float(suite_reports_14d[i].pass_rate) / 100)
      sheet_row.set("-14d", float(suite_reports_21d[i].pass_rate) / 100)
      sheet_row.set("-21d", float(suite_reports_28d[i].pass_rate) / 100)

   sheet.commitChanges()
   print(f"Succesfully updated \"{sheet.name()}\" sheet")


class LineWrapRawTextHelpFormatter(argparse.RawDescriptionHelpFormatter):
   def _split_lines(self, text, width):
      text = self._whitespace_matcher.sub(" ", text).strip()
      return _textwrap.wrap(text, 55)


fboss_suite_rp_ssid = "1rxbJpzKbnVXoMFdHTLBD-GX1pi-NZGJA5LROdPwJ054"
parser = argparse.ArgumentParser(
   description="Update FBOSS Ship Report Spreedsheet at go/fboss-shipreport \n\n"
   "By default suite report and test runs are limited to pass 7 days\n\n"
   "To use your own spreadsheet:\n"
   "  1. Create a spreadsheet with new worksheets, and make the\n"
   "     spreadsheet world writeable.\n\n"
   "  2. Create a suite report worksheet with the following columns \n"
   "       Suite, Full Name, Runs, Passes, Fails, \n"
   "       Pass%, Residual Pass%, Coverage\n\n"
   "  3. Create a test run worksheet with the following columns \n"
   "       Test Name, Pass%, Runs, Passes, Fails, Timeouts\n\n"
   "  4. Run the tool providing your spreadsheet ID and worksheet names\n\n",
   formatter_class=LineWrapRawTextHelpFormatter,
)
parser.add_argument("CONTAINER", action="store", help="container name")
parser.add_argument("HOST", action="store", help="full container hostname")
parser.add_argument(
   "-s", "--spreadsheet",
   action="store",
   required=False,
   help="Key to Google spreadsheet"
   " in https://docs.google.com/spreadsheets/d/<key>/edit",
   default=fboss_suite_rp_ssid,
)
parser.add_argument(
   "-w", "--worksheets",
   action="store",
   required=False,
   nargs=3,
   help="Name of worksheets within spreadsheet to store data to.\n",
   default=["FBOSS Ship Report (7d)",
            "FBOSS Ship Test Runs (7d)",
            "FBOSS Ship Pass Rate History"],
)
parser.add_argument(
   "-p", "--project",
   action="store",
   required=False,
   help="Project name. Default: fboss_schedule_autotest",
   default="fboss_schedule_autotest",
)

if __name__ == '__main__':
   args = parser.parse_args()

   # --- Generate suite reports ---
   generate_suite_reports(args.CONTAINER, args.HOST, args.project)

   # --- Parse suite report json and csv files ---
   suite_report_dir = "fboss-suite-reports"
   suite_reports_all = []

   for i, limit in enumerate(limits):
      suite_reports = []
      for j, suite in enumerate(suites):
         base_suite_name = suite[0]
         suite_name = "_".join(suite)
         json_file = f"{suite_report_dir}/{limit}/{suite_name}_report.json"
         test_run_csv_file = f"{suite_report_dir}/{limit}/{suite_name}_test_runs.csv"

         with open(json_file) as json_data:
            data = json.load(json_data)
            suite_rp = SuiteReport.from_json(data[f"FbossTest/{base_suite_name}"])
            suite_rp.set_custom_name(suite_name)
            # we only get detailed test runs for 7d
            if limit == '7d':
               suite_rp.add_tests_from_csv(test_run_csv_file)

            # calculate non-overlapping pass% for every 7 days chunk
            if i > 0:
               new_passed = suite_rp.passed - suite_reports_all[i - 1][j].passed
               new_failed = suite_rp.failed - suite_reports_all[i - 1][j].failed
               suite_rp.update_passed_failed(new_passed, new_failed)

            suite_reports.append(suite_rp)
      suite_reports_all.append(suite_reports)

   # --- Get latest build info ---
   build_info = get_latest_build_info(args.project)

   print("--- Updating Spreadsheet ---")
   service = SpreadsheetLibV5.Service()
   spd = service.getSpreadsheet(args.spreadsheet)
   ship_rp_sheet = spd.sheet(args.worksheets[0])
   assert ship_rp_sheet, f"no sheet with name {args.worksheets[0]}"
   test_run_sheet = spd.sheet(args.worksheets[1])
   assert test_run_sheet, f"no sheet with name {args.worksheets[1]}"
   pass_rate_hist_sheet = spd.sheet(args.worksheets[2])
   assert pass_rate_hist_sheet, f"no sheet with name {args.worksheets[2]}"

   update_7d_suite_report_sheet(ship_rp_sheet, suite_reports_all[0], build_info)
   update_7d_test_run_sheet(test_run_sheet, suite_reports_all[0])
   update_pass_rate_history_sheet(pass_rate_hist_sheet, suite_reports_all)

   print(
      "Successfully updated spreadsheet at "
      f"https://docs.google.com/spreadsheets/d/{args.spreadsheet}/edit"
   )
