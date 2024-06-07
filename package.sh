#!/bin/bash

set -e

FBOSS_REPO=$(pwd)

FBOSS_REPO_RPM_DIR="$FBOSS_REPO/arista/rpm"
RPM_DIR="/tmp/rpmbuild/RPMS/x86_64"
ARCH=$1
KERNEL=$2
FBOSS_RPM_DIR="$DESTDIR/usr/share/ptest-data/Fboss/RPMS/$ARCH/$KERNEL"
RPMS=()

if [ $KERNEL = "4.18" ]; then
   export KERNEL_SRC="4.18.0-408.el8.x86_64"
elif [ $KERNEL = "5.12" ]; then
   export KERNEL_SRC="5.12.0-0_fbk2_3390_g7ecb4ac46d7f"
else
   export KERNEL_SRC="5.19.0"
fi

mkdir -p /tmp/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS,BUILDROOT}
echo "FBOSS_RPM_DIR $FBOSS_RPM_DIR"
mkdir -p $FBOSS_RPM_DIR

mkdir -p fboss.git
cp -r arista fboss.git
cp -r /src/dest/tmp_build_dir .

# Find the RPMs to build.
RPMS=($(find "${FBOSS_REPO_RPM_DIR}" -type f -name *.spec))

# Avoid packaging kmods for kernel versinos 4.18 and 5.12
FILTERED_RPMS=()
if [ "$KERNEL" == "4.18" ] || [ "$KERNEL" == "5.12" ]; then
   for rpm in "${RPMS[@]}"; do
      if [[ "$rpm" != *"arista_bsp_kmods.spec" ]]; then
         FILTERED_RPMS+=("$rpm")
      fi
   done
   RPMS=("${FILTERED_RPMS[@]}")
fi

mkdir -p $FBOSS_REPO/Aqua_SAI/sdk-src/tools/sand
cp -r /src/dest/db $FBOSS_REPO/Aqua_SAI/sdk-src/tools/sand

for rpm in "${RPMS[@]}"; do
    rpmbuild -v --define '_topdir /tmp/rpmbuild' -bb "${rpm}" --root /tmp --define 'root /tmp'
    built_rpm=$(find "${RPM_DIR}" -type f -name "$(basename ${rpm%.*})*")
    cp -f "${built_rpm}" "${FBOSS_RPM_DIR}"
done
