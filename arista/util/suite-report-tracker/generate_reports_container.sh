#!/bin/bash
#
# -------------------------------------------------------------------------
#
# Usage: 
#   1. Copy generate_reports_container.sh into somewhere in home directory
#   2. a4c shell <container> <path to generate_reports_container.sh>
#
# Description: 
#   Generate FBOSS suite reports. Reports are generated
#   to /home/<user>/tmp/fboss-suite-reports
#
# --------------------------------------------------------------------------

# --- Configuration ---
reports_dir="$HOME/tmp/fboss-suite-reports"
project="fboss_schedule_autotest"
limits=("7d" "14d" "21d" "28d")

# --- Generate Suite Report Files in Container ---
for limit in "${limits[@]}"; do
  output_dir="$reports_dir/$limit"
  rm -rf $output_dir
  mkdir -p $output_dir
  a suite rp FbossTest/FbossOssViperShip -p $project -m $limit -c -L 1 --json > $output_dir/FbossOssViperShip_report.json
  a suite rp FbossTest/FbossOssViperBShip -p $project -m $limit -c -L 1 --json > $output_dir/FbossOssViperBShip_report.json
  a suite rp FbossTest/FbossOssViperCShip -p fboss-j3plus -m $limit -c -L 1 --json > $output_dir/FbossOssViperCShip_report.json
  a suite rp FbossTest/FbossOssWhistlerShip -p $project -m $limit -c -L 1 --json > $output_dir/FbossOssWhistlerShip_report.json
  a suite rp FbossTest/FbossRackhawkShip -p $project -m $limit -c -L 1 --json > $output_dir/FbossRackhawkShip_report.json
  a suite rp FbossTest/FbossRackhawkShip -p $project -m $limit -d rkdo -c -L 1 --json > $output_dir/FbossRackhawkShip_rkdo_report.json
  a suite rp FbossTest/FbossOssShip -p $project -m $limit -d qsfb -c -L 1 --json > $output_dir/FbossOssShip_qsfb_report.json
done

# --- Only Generate detailed test runs for past 7 days ---
output_dir="$reports_dir/7d"
echo $output_dir
a suite rp FbossTest/FbossOssViperShip -p $project -m 7d --cr $output_dir/FbossOssViperShip_test_runs.csv
a suite rp FbossTest/FbossOssViperBShip -p $project -m 7d --cr $output_dir/FbossOssViperBShip_test_runs.csv
a suite rp FbossTest/FbossOssViperCShip -p fboss-j3plus -m 7d --cr $output_dir/FbossOssViperCShip_test_runs.csv
a suite rp FbossTest/FbossOssWhistlerShip -p $project -m 7d --cr $output_dir/FbossOssWhistlerShip_test_runs.csv
a suite rp FbossTest/FbossRackhawkShip -p $project -m 7d --cr $output_dir/FbossRackhawkShip_test_runs.csv
a suite rp FbossTest/FbossRackhawkShip -p $project -m 7d -d rkdo --cr $output_dir/FbossRackhawkShip_rkdo_test_runs.csv
a suite rp FbossTest/FbossOssShip -p $project -m 7d -d qsfb --cr $output_dir/FbossOssShip_qsfb_test_runs.csv
