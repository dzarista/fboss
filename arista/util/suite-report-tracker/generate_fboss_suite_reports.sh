#!/bin/bash

# --- Configuration ---
util_dir=$(dirname "$(realpath "$0")")
remote_reports_dir="/user/tmp/fboss-suite-reports"
local_reports_dir="$util_dir/fboss-suite-reports"

remote_user=$(whoami)
container_hostname=$1
project=$2
limits=("7d" "14d" "21d" "28d")

# --- Generate Suite Report Files in Container ---
for limit in "${limits[@]}"; do
  output_dir="$remote_reports_dir/$limit"
  
  ssh "$remote_user@$container_hostname" "
    rm -rf '$output_dir'
    mkdir -p '$output_dir'
    a suite rp FbossTest/FbossOssViperShip -p $project -m $limit -c -L 1 --json > $output_dir/FbossOssViperShip_report.json
    a suite rp FbossTest/FbossOssViperBShip -p $project -m $limit -c -L 1 --json > $output_dir/FbossOssViperBShip_report.json
    a suite rp FbossTest/FbossOssWhistlerShip -p $project -m $limit -c -L 1 --json > $output_dir/FbossOssWhistlerShip_report.json
    a suite rp FbossTest/FbossRackhawkShip -p $project -m $limit -c -L 1 --json > $output_dir/FbossRackhawkShip_report.json
    a suite rp FbossTest/FbossRackhawkShip -p $project -m $limit -d rkdo -c -L 1 --json > $output_dir/FbossRackhawkShip_rkdo_report.json
    a suite rp FbossTest/FbossOssShip -p $project -m $limit -d qsfb -c -L 1 --json > $output_dir/FbossOssShip_qsfb_report.json
  "
done

# --- Only Generate detailed test runs for past 7 days ---
output_dir="$remote_reports_dir/7d"
ssh "$remote_user@$container_hostname" "
  a suite rp FbossTest/FbossOssViperShip -p $project -m 7d --cr $output_dir/FbossOssViperShip_test_runs.csv
  a suite rp FbossTest/FbossOssViperBShip -p $project -m 7d --cr $output_dir/FbossOssViperBShip_test_runs.csv
  a suite rp FbossTest/FbossOssWhistlerShip -p $project -m 7d --cr $output_dir/FbossOssWhistlerShip_test_runs.csv
  a suite rp FbossTest/FbossRackhawkShip -p $project -m 7d --cr $output_dir/FbossRackhawkShip_test_runs.csv
  a suite rp FbossTest/FbossRackhawkShip -p $project -m 7d -d rkdo --cr $output_dir/FbossRackhawkShip_rkdo_test_runs.csv
  a suite rp FbossTest/FbossOssShip -p $project -m 7d -d qsfb --cr $output_dir/FbossOssShip_qsfb_test_runs.csv
"

# --- Copy suite report files ---
echo "--- Copying contents of $container_hostname:$remote_reports_dir to $local_reports_dir ---"
rm -rf "$local_reports_dir"
mkdir -p "$local_reports_dir"
scp -r "$remote_user@$container_hostname:$remote_reports_dir/*" "$local_reports_dir"

# -- Clean up on remote --
ssh "$remote_user@$container_hostname" "
  rm -rf '$remote_reports_dir'
"
