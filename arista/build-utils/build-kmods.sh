#!/bin/bash

set -e

UTIL_DIR=$(dirname "$(realpath "$0")")
KMODS_DIR=$(realpath "$UTIL_DIR/../../fboss.bsp.arista/bsp-kmods")
RPM_DIR=$(realpath "$UTIL_DIR/../rpm")

BUILD_DIR="$UTIL_DIR/tmp_build_dir/fboss.bsp.arista"
mkdir -p $BUILD_DIR
KERNEL=$1

usage() {
    echo "Usage: $0 <Kernel Version>"
    echo
    echo "Options:"
    echo "  -h, --help           Display this help message and exit."
    echo
    echo "This script builds and packages the kmods in arista/bsp-kmods into an RPM in your workspace"
}

if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    usage
    exit 0
fi

if [ "$KERNEL" = "4.18" ]; then
   export KERNEL_SRC="4.18.0-408.el8.x86_64"
elif [ "$KERNEL" = "5.12" ]; then
   export KERNEL_SRC="5.12.0-0_fbk2_3390_g7ecb4ac46d7f"
elif [ "$KERNEL" = "5.19" ]; then
   export KERNEL_SRC="5.19.0"
else
   export KERNEL_SRC="6.4.3-0_fbk747_rc2_1199_ga95cd85c72c4"
fi

if [ ! -d "$BUILD_DIR/$KERNEL_SRC" ]; then
    # Download fboss kernel src
    KERNEL_SRC_TAR=FBOSS_KERNEL_SRC_"${KERNEL_SRC}".tar.gz
    wget -P $BUILD_DIR/downloads http://dist/storage/fboss/fbossImageFiles/"${KERNEL_SRC_TAR}"
    tar -xf $BUILD_DIR/downloads/"${KERNEL_SRC_TAR}" -C $BUILD_DIR
fi

echo "Copying bsp-kmods to tmp_build_dir"
rm -rf $BUILD_DIR/bsp-kmods
cp -rf $KMODS_DIR $BUILD_DIR/bsp-kmods

echo "Building bsp-kmods..."
make -C $BUILD_DIR/$KERNEL_SRC M=$BUILD_DIR/bsp-kmods modules

echo "Packaging bsp-kmods into RPM"
rpmbuild -bb "$RPM_DIR/arista_bsp_kmods.spec" --define "_topdir $BUILD_DIR/$KERNEL_SRC" \
         --define "_fboss_dir $BUILD_DIR/.."
