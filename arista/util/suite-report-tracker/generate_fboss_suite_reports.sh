#!/bin/bash

# Usage:
#  1. Copy generate_reports_container.sh into a container at:
#       /user/suite-report-tracker/generate_reports_container.sh
#  2. To generate reports and update tracker spreadsheet (can be a cron job):
#       /usr/bin/python3 UpdateFbossReportSpreadsheet.py <container>

# --- Configuration ---
util_dir=$(dirname "$(realpath "$0")")
remote_reports_dir="/user/suite-report-tracker/fboss-suite-reports"
local_reports_dir="$util_dir/fboss-suite-reports"

remote_user=$(whoami)
container_name=$1
container_hostname=$2

# --- Generate Suite Report Files in Container ---
echo "--- Generating suite reports in container, this might take a while... ---"
a4c shell --exec $container_name /user/suite-report-tracker/generate_reports_container.sh

# --- Copy suite report files ---
echo "--- Copying contents of $container_hostname:$remote_reports_dir to $local_reports_dir ---"
rm -rf "$local_reports_dir"
mkdir -p "$local_reports_dir"
scp -r "$remote_user@$container_hostname:$remote_reports_dir/*" "$local_reports_dir"
