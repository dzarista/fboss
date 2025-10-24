#!/bin/bash

echo "Beginning SWI build"

ARCH=$1
KERNEL=$2
TARGET_DIR=$3
RPM_DIR=$4

if [ $KERNEL = "6.4" ]; then
    TARBALL="centos9_6.4.3-0_fbk747_rc2_1199_ga95cd85c72c4_live.tar"
elif [ $KERNEL = "6.11" ]; then
    TARBALL="centos9_6.11.1-0_fbk9_0_g2bb6f7f1c90e_live.tar"
elif [ $KERNEL = "6.11_amd" ]; then
    TARBALL="centos9_6.11.0_amd_live.tar"
else
    echo "Unsupported kernel version"
    exit 1
fi

mkdir -p $TARGET_DIR

cd $TARGET_DIR
touch version
# Version placeholder until we can find a way to inject git commit-hash
echo "SWI_VERSION=42.0.0" > version
echo "BUILD_DATE=$(date -u +"%Y%m%dT%H%M%SZ")" >> version
echo "SWI_VARIANT=US" >> version
echo "KERNEL_VERSION=$KERNEL" >> version

wget -q http://dist/storage/fboss/"${TARBALL}"
tar -xf "$TARBALL"

cp boot/initramfs* boot/squashfs.img boot/vmlinuz* .
rm -rf boot
rm -rf "$TARBALL"

FBOSS_PTEST_DATA_DIR="/usr/share/ptest-data/Fboss"
FBOSS_CORE_RPM_DIR="$FBOSS_PTEST_DATA_DIR/RPMS/core_$ARCH"
FBOSS_KMOD_DIR="$FBOSS_PTEST_DATA_DIR/RPMS/kmods_$KERNEL"
FBOSS_PLATFORM_RPM_DIR="$FBOSS_PTEST_DATA_DIR/RPMS/platform"
FBOSS_SWI_MODULES_DIR="$FBOSS_PTEST_DATA_DIR/swi-modules"

cp -a "${FBOSS_SWI_MODULES_DIR}/." $TARGET_DIR
rm -rf "build_swi.sh"
if ! [ -z "${RPM_DIR}" ]; then
    cp -a "${RPM_DIR}/." $TARGET_DIR
else
    cp -a "${FBOSS_CORE_RPM_DIR}/." $TARGET_DIR
    cp -a "${FBOSS_PLATFORM_RPM_DIR}/." $TARGET_DIR
    cp -a "${FBOSS_KMOD_DIR}/." $TARGET_DIR
fi

zip FBOSS.swi *

find "$TARGET_DIR" -type f ! -name "FBOSS.swi" -delete
