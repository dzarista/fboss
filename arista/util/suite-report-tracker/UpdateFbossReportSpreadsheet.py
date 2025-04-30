import sys
import argparse
import textwrap as _textwrap
import csv
import json
import subprocess
import SpreadsheetLibV5
import datetime
import pytz


def string_to_bool(s):
   s = s.lower()
   if s == "true":
      return True
   elif s == "false":
      return False
   else:
      raise ValueError("Invalid boolean string")


def string_to_int_empty_as_zero(val):
   if val == "":
      return 0
   return int(val)


class TestRun:
   def __init__(self, has_run, suite, package, test, aggregate, test_type,
                passes, fails, NAs, timeouts, last_result, last_date,
                last_build_version, variants):
      self.has_run = string_to_bool(has_run)
      self.suite = suite
      self.package = package
      self.test_name = test
      self.test_type = test_type
      self.aggregate = string_to_bool(aggregate)
      self.last_result = last_result
      self.last_date = last_date
      self.last_build_version = last_build_version
      self.variants = variants
      self.passes = string_to_int_empty_as_zero(passes)
      self.fails = string_to_int_empty_as_zero(fails)
      self.NAs = string_to_int_empty_as_zero(NAs)
      self.timeouts = string_to_int_empty_as_zero(timeouts)
      self.runs = self.passes + self.fails + self.timeouts
      self.pass_rate = self.passes / self.runs if self.runs else 0


class SuiteReport:
   def __init__(self, fullname, runs, passed, failed, pass_rate,
                residual_pass_rate, coverage, children=None):
      # These fields are populated by 'a suite report --json' json file
      self.fullname = fullname
      self.runs = runs
      self.passed = passed
      self.failed = failed
      self.pass_rate = pass_rate
      self.residual_pass_rate = residual_pass_rate
      self.coverage = coverage
      self.children = [] if children is None else children

      # Tests are populated by 'a suite report --cr' csv file
      self.test_runs = []

   @classmethod
   def from_json(cls, json_data):
      if isinstance(json_data, dict):
         suite_rp = cls(
               json_data["full_name"],
               json_data["runs"],
               json_data["passed"],
               json_data["failed"],
               json_data["pass%"],
               json_data["residual_pass%"],
               json_data["coverage"],
         )
         for child_data in json_data["children"]:
            child_node = cls.from_json(child_data)
            suite_rp.children.append(child_node)
         return suite_rp
      else:
         raise ValueError("Unexpected JSON data format")

   def add_tests_from_csv(self, csv_file):
      with open(csv_file, "r") as csvfile:
         reader = csv.DictReader(csvfile)
         for row in reader:
            if not bool(string_to_bool(row["aggregate"])):
               test_run = TestRun(**row)
               self.test_runs.append(test_run)


class LineWrapRawTextHelpFormatter(argparse.RawDescriptionHelpFormatter):
   def _split_lines(self, text, width):
      text = self._whitespace_matcher.sub(" ", text).strip()
      return _textwrap.wrap(text, 55)


fboss_suite_rp_ssid = "1rxbJpzKbnVXoMFdHTLBD-GX1pi-NZGJA5LROdPwJ054"
parser = argparse.ArgumentParser(
   description="Update FBOSS Ship Report Spreedsheet at\n\n"
   f"  https://docs.google.com/spreadsheets/d/{fboss_suite_rp_ssid}/edit \n\n"
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
   nargs=2,
   help="Name of worksheets within spreadsheet to store data to.\n"
   "Default: fboss ship reports, fboss ship test runs",
   default=["fboss ship reports", "fboss ship test runs"],
)
parser.add_argument(
   "-p", "--project",
   action="store",
   required=False,
   help="Project name. Default: fboss_schedule_autotest",
   default="fboss_schedule_autotest",
)
parser.add_argument(
   "-m", "--limit",
   action="store",
   required=False,
   help="Limit to LIMIT tests. Default: 7d",
   default="7d",
)
args = parser.parse_args()

# --- Generate suite report json and csv files ---
script_path = "./generate_fboss_suite_reports.sh"
try:
   command = [script_path, args.HOST, args.project, args.limit]
   result = subprocess.run(command, check=True)
   print("Sucessfully generated suite reports")
except subprocess.CalledProcessError as e:
   print(f"Error: error while generating suite reports: {e}", file=sys.stderr)
   sys.exit(1)
except FileNotFoundError:
   print(f"Error: Script not found at {script_path}", file=sys.stderr)
   sys.exit(1)

# --- Parse suite report json and csv files ---
suites = [
   ["FbossOssViperShip"],
   ["FbossOssViperBShip"],
   ["FbossOssWhistlerShip"],
   ["FbossRackhawkShip"],
   ["FbossRackhawkShip", "rkdo"],
   ["FbossOssShip", "qsfb"],
]
suite_report_dir = "fboss-suite-reports"
suite_reports = []

for suite in suites:
   base_suite_name = suite[0]
   suite_name = "_".join(suite)
   json_file = f"{suite_report_dir}/{suite_name}_report.json"
   test_run_csv_file = f"{suite_report_dir}/{suite_name}_test_runs.csv"

   with open(json_file) as json_data:
      data = json.load(json_data)
      suite_rp = SuiteReport.from_json(data[f"FbossTest/{base_suite_name}"])
      suite_rp.add_tests_from_csv(test_run_csv_file)
      suite_reports.append((suite_name, suite_rp))

# --- Updating Spreadsheet ---
print("--- Updating Spreadsheet ---")
service = SpreadsheetLibV5.Service()
spd = service.getSpreadsheet(args.spreadsheet)
ship_rp_sheet = spd.sheet(args.worksheets[0])
assert ship_rp_sheet, f"no sheet with name {args.worksheets[0]}"
test_run_sheet = spd.sheet(args.worksheets[1])
assert test_run_sheet, f"no sheet with name {args.worksheets[1]}"

# --- write to ship report sheet ---
ship_rp_sheet.setKeyCol("Suite")
for suite, suite_rp in suite_reports:
   sheet_row = ship_rp_sheet.getRow(suite)
   if not sheet_row:
      sheet_row = ship_rp_sheet.addRow(suite)

   sheet_row.set("Full Name", suite_rp.fullname)
   sheet_row.set("Runs", int(suite_rp.runs))
   sheet_row.set("Passes", int(suite_rp.passed))
   sheet_row.set("Fails", int(suite_rp.failed))
   sheet_row.set("Pass%", float(suite_rp.pass_rate) / 100)
   sheet_row.set("Residual Pass%", float(suite_rp.residual_pass_rate) / 100)
   sheet_row.set("Coverage", float(suite_rp.coverage) / 100)

ship_rp_sheet.commitChanges()
ship_rp_sheet.sort("Pass%", ascending=False)
print(f"Succesfully updated \"{ship_rp_sheet.name()}\" sheet")

# --- write to test run sheet ---
test_run_sheet.setKeyCol("Test Name")
all_rows = test_run_sheet.getRows()

# set Last Updated row
now_est = datetime.datetime.now(pytz.timezone('US/Eastern'))
formatted_now = now_est.strftime('%Y-%m-%d %H:%M:%S %Z%z')
last_updated_str = f"Last updated: {formatted_now}"
if all_rows:
   last_updated_row = all_rows[0]
   last_updated_row.set("Test Name", last_updated_str)
else:
   last_updated_row = test_run_sheet.addRow(last_updated_str)

# clear test run rows
for row in all_rows[1:]:
   test_run_sheet.deleteRow(row)

test_run_sheet.commitChanges()

for suite, suite_rp in suite_reports:
   test_run_sheet.addRow(f"{suite} Test Runs ({args.limit})")
   for test_run in suite_rp.test_runs:
      row_key = f"{suite}::{test_run.test_name}"

      sheet_row = test_run_sheet.addRow(row_key)
      sheet_row.set("Pass%", test_run.pass_rate)
      sheet_row.set("Runs", test_run.runs)
      sheet_row.set("Passes", test_run.passes)
      sheet_row.set("Fails", test_run.fails)
      sheet_row.set("Timeouts", test_run.timeouts)

test_run_sheet.commitChanges()

print(f"Succesfully updated \"{test_run_sheet.name()}\" sheet")

print(
   "Successfully updated spreadsheet at "
   f"https://docs.google.com/spreadsheets/d/{args.spreadsheet}/edit"
)
