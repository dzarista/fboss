#!/bin/bash

# Usage:
#  1. Copy generate_reports_container.sh into a container at:
#       /user/suite-report-tracker/generate_reports_container.sh
#  2. To generate reports and update tracker spreadsheet (can be a cron job):
#       /usr/bin/python3 UpdateFbossReportSpreadsheet.py <container> <container-hostname>

# --- Configuration ---
util_dir=$(dirname "$(realpath "$0")")
remote_reports_dir="$util_dir/fboss-suite-reports"
project="fboss_schedule_autotest"
limits=("7d" "14d" "21d" "28d")

# --- Generate Suite Report Files in Container ---
for limit in "${limits[@]}"; do
  output_dir="$remote_reports_dir/$limit"
  rm -rf $output_dir
  mkdir -p $output_dir
  a suite rp FbossTest/FbossOssViperShip -p $project -m $limit -c -L 1 --json > $output_dir/FbossOssViperShip_report.json
  a suite rp FbossTest/FbossOssViperBShip -p $project -m $limit -c -L 1 --json > $output_dir/FbossOssViperBShip_report.json
  a suite rp FbossTest/FbossOssWhistlerShip -p $project -m $limit -c -L 1 --json > $output_dir/FbossOssWhistlerShip_report.json
  a suite rp FbossTest/FbossRackhawkShip -p $project -m $limit -c -L 1 --json > $output_dir/FbossRackhawkShip_report.json
  a suite rp FbossTest/FbossRackhawkShip -p $project -m $limit -d rkdo -c -L 1 --json > $output_dir/FbossRackhawkShip_rkdo_report.json
  a suite rp FbossTest/FbossOssShip -p $project -m $limit -d qsfb -c -L 1 --json > $output_dir/FbossOssShip_qsfb_report.json
done

# --- Only Generate detailed test runs for past 7 days ---
output_dir="$remote_reports_dir/7d"
a suite rp FbossTest/FbossOssViperShip -p $project -m 7d --cr $output_dir/FbossOssViperShip_test_runs.csv
a suite rp FbossTest/FbossOssViperBShip -p $project -m 7d --cr $output_dir/FbossOssViperBShip_test_runs.csv
a suite rp FbossTest/FbossOssWhistlerShip -p $project -m 7d --cr $output_dir/FbossOssWhistlerShip_test_runs.csv
a suite rp FbossTest/FbossRackhawkShip -p $project -m 7d --cr $output_dir/FbossRackhawkShip_test_runs.csv
a suite rp FbossTest/FbossRackhawkShip -p $project -m 7d -d rkdo --cr $output_dir/FbossRackhawkShip_rkdo_test_runs.csv
a suite rp FbossTest/FbossOssShip -p $project -m 7d -d qsfb --cr $output_dir/FbossOssShip_qsfb_test_runs.csv
