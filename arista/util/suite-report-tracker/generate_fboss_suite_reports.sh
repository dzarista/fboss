#!/bin/bash

# --- Configuration ---
util_dir=$(dirname "$(realpath "$0")")
remote_reports_dir="/user/tmp/fboss-suite-reports"
local_reports_dir="$util_dir/fboss-suite-reports"

remote_user=$(whoami)
container_hostname=$1
project=$2
limit=$3

# --- Generate Suite Report Files in Container ---
echo "--- Generating suite reports on $container_hostname ---"
ssh "$remote_user@$container_hostname" "
  rm -rf '$remote_reports_dir'
  mkdir -p '$remote_reports_dir'

  a suite rp FbossTest/FbossOssViperShip -p $project -m $limit -c --json > $remote_reports_dir/FbossOssViperShip_report.json
  a suite rp FbossTest/FbossOssViperShip -p $project -m $limit --cr $remote_reports_dir/FbossOssViperShip_test_runs.csv

  a suite rp FbossTest/FbossOssViperBShip -p $project -m $limit -c --json > $remote_reports_dir/FbossOssViperBShip_report.json
  a suite rp FbossTest/FbossOssViperBShip -p $project -m $limit --cr $remote_reports_dir/FbossOssViperBShip_test_runs.csv

  a suite rp FbossTest/FbossOssWhistlerShip -p $project -m $limit -c --json > $remote_reports_dir/FbossOssWhistlerShip_report.json
  a suite rp FbossTest/FbossOssWhistlerShip -p $project -m $limit --cr $remote_reports_dir/FbossOssWhistlerShip_test_runs.csv

  a suite rp FbossTest/FbossRackhawkShip -p $project -m $limit -c --json > $remote_reports_dir/FbossRackhawkShip_report.json
  a suite rp FbossTest/FbossRackhawkShip -p $project -m $limit --cr $remote_reports_dir/FbossRackhawkShip_test_runs.csv

  a suite rp FbossTest/FbossRackhawkShip -p $project -m $limit -d rkdo -c --json > $remote_reports_dir/FbossRackhawkShip_rkdo_report.json
  a suite rp FbossTest/FbossRackhawkShip -p $project -m $limit -d rkdo --cr $remote_reports_dir/FbossRackhawkShip_rkdo_test_runs.csv
  
  a suite rp FbossTest/FbossOssShip -p $project -m $limit -d qsfb -c --json > $remote_reports_dir/FbossOssShip_qsfb_report.json
  a suite rp FbossTest/FbossOssShip -p $project -m $limit -d qsfb --cr $remote_reports_dir/FbossOssShip_qsfb_test_runs.csv
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
