#!/bin/bash

echo "Beginning SWI build"

ARCH=$1
KERNEL=$2
FBOSS_REPO=$SRCDIR_0

mkdir -p "${FBOSS_REPO}/tmp"

SCRATCH_DIR="${FBOSS_REPO}/tmp"

if [ $KERNEL = "6.4" ]; then
    TARBALL="centos9_6.4.3-0_fbk747_rc2_1199_ga95cd85c72c4_live.tar"
else
    echo "Unspported kernel version"
    exit 1
fi

cd "$SCRATCH_DIR"

touch version
GIT_COMMIT_HASH_7_DIGITS=$(echo "${SRC_0}" | grep -o '#[^#]*$' | tr -dc '0-9' | cut -c-7)
echo "SWI_VERSION=${GIT_COMMIT_HASH_7_DIGITS}" > version
echo "BUILD_DATE=$(date -u +"%Y%m%dT%H%M%SZ")" >> version
echo "SWI_VARIANT=US" >> version
echo "KERNEL_VERSION=6.4" >> version

cat version

wget -q http://dist/storage/fboss/"${TARBALL}"
tar -xf "$TARBALL"

cp boot/initramfs* boot/squashfs.img boot/vmlinuz* .
rm -rf boot
rm -rf "$TARBALL"

cp -a "${FBOSS_REPO}/swi-modules/." .

FBOSS_PTEST_DATA_DIR="/src/dest/usr/share/ptest-data/Fboss"
FBOSS_RPM_DIR="$FBOSS_PTEST_DATA_DIR/RPMS/$ARCH/$KERNEL"

cp -a "${FBOSS_RPM_DIR}/." .

zip FBOSS.swi *

unzip -l FBOSS.swi

results="${DESTDIR}/usr/share/ptest-data/Fboss"
mkdir -p "$results"
cp FBOSS.swi "$results"
cp -r "$FBOSS_PTEST_DATA_DIR"/* "$results"
