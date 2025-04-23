#!/bin/bash

set -e

UTIL_DIR=$(dirname "$(realpath "$0")")
SHOWTECH_DIR=$(realpath "$UTIL_DIR/../../fboss.bsp.arista/showtech")
RPM_DIR=$(realpath "$UTIL_DIR/../rpm")

BUILD_DIR="$UTIL_DIR/tmp_build_dir/fboss.bsp.arista"
mkdir -p $BUILD_DIR

usage() {
    echo "Usage: $0"
    echo
    echo "Options:"
    echo "  -h, --help           Display this help message and exit."
    echo
    echo "This script builds and packages showtech"
}

if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    usage
    exit 0
fi

echo "Copying showtech to tmp_build_dir"
rm -rf $BUILD_DIR/showtech
cp -rf $SHOWTECH_DIR $BUILD_DIR/showtech

echo "Building showtech..."
make -C $BUILD_DIR/showtech

echo "Packaging showtech into RPM"
rpmbuild -bb "$RPM_DIR/showtech-arista.spec" --define "_topdir $BUILD_DIR" \
         --define "_fboss_dir $BUILD_DIR/.."
