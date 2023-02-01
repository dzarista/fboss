#!/bin/bash
# Package FBOSS OSS into RPMs. RPMs to build can be specified as input. If not
# RPMs are given, all will be rebuilt.

if [[ ! -f /.dockerenv ]]; then
   echo "Please run this script from within the docker build container."
fi

FBOSS_REPO_RPM_DIR="/var/FBOSS/fboss.git/arista/rpm"
FBOSS_RPM_DIR="/var/FBOSS/rpmbuild/RPMS/"
RPM_DIR="/root/rpmbuild/RPMS/x86_64"
RPMS=()
set -ex

mkdir -p "${FBOSS_RPM_DIR}"

# Find the RPMs to build.
if [[ $# -lt 1 ]]; then
   RPMS=($(find "${FBOSS_REPO_RPM_DIR}" -type f -name *.spec))
else
   for rpm in "${@}"; do
      RPMS+=("${FBOSS_REPO_RPM_DIR}/${rpm}.spec")
   done
fi

for rpm in "${RPMS[@]}"; do
   rpmbuild -bb "${rpm}"
   built_rpm=$(find "${RPM_DIR}" -type f -name "$(basename ${rpm%.*})*")
   cp -f "${built_rpm}" "${FBOSS_RPM_DIR}"
done
