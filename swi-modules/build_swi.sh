#!/bin/bash

echo "Beginning SWI build"

ARCH=$1
KERNEL=$2
TARGET_DIR=$3

if [ $KERNEL = "6.4" ]; then
    TARBALL="centos9_6.4.3-0_fbk747_rc2_1199_ga95cd85c72c4_live.tar"
else
    echo "Unspported kernel version"
    exit 1
fi

mkdir -p $TARGET_DIR

cd $TARGET_DIR
touch version
# Version placeholder until we can find a way to inject git commit-hash
echo "SWI_VERSION=42.0.0" > version
echo "BUILD_DATE=$(date -u +"%Y%m%dT%H%M%SZ")" >> version
echo "SWI_VARIANT=US" >> version
echo "KERNEL_VERSION=6.4" >> version

wget -q http://dist/storage/fboss/"${TARBALL}"
tar -xf "$TARBALL"

cp boot/initramfs* boot/squashfs.img boot/vmlinuz* .
rm -rf boot
rm -rf "$TARBALL"

FBOSS_PTEST_DATA_DIR="/usr/share/ptest-data/Fboss"
FBOSS_RPM_DIR="$FBOSS_PTEST_DATA_DIR/RPMS/$ARCH/$KERNEL"
FBOSS_SWI_MODULES_DIR="$FBOSS_PTEST_DATA_DIR/swi-modules"

cp -a "${FBOSS_SWI_MODULES_DIR}/." $TARGET_DIR
rm -rf "build_swi.sh"
cp -a "${FBOSS_RPM_DIR}/." $TARGET_DIR

zip FBOSS.swi *

find "$TARGET_DIR" -type f ! -name "FBOSS.swi" -delete
