#!/bin/bash

set -e

FBOSS_DIR=/tmp
FBOSS_REPO=$SRCDIR_0
SAI_DIR=/src/dest/result
SCRATCH_DIR="$FBOSS_DIR/tmp_build_dir"

# workaround: barney doesn't process git files, so we need
# simulated that .git dir exist for copytree.py:containing_repo_type
touch ".git"

# Optionally, pin the fboss and its dependencies to known
# stable commit hash
rm -rf build/deps/github_hashes/facebook
rm -rf build/deps/github_hashes/facebookincubator
tar -xvf fboss/oss/stable_commits/latest_stable_hashes.tar.gz --no-same-owner

mkdir -p $FBOSS_DIR/built-sai/experimental
mkdir -p $FBOSS_DIR/built-bcm-sai
cp $SAI_DIR/libraries/libsai.a $FBOSS_DIR/built-bcm-sai/libsai_impl.a
cp $SAI_DIR/include/*.* $FBOSS_DIR/built-sai/experimental
cd $FBOSS_REPO/fboss/oss/scripts
./build-helper.py $FBOSS_DIR/built-bcm-sai/libsai_impl.a \
   $FBOSS_DIR/built-sai/experimental/ $FBOSS_DIR/sai_impl_output

# Build FBOSS
export SAI_ONLY=1
export SAI_BRCM_IMPL=1 # Needed only for BRCM SAI
export GETDEPS_USE_WGET=1
cd "$FBOSS_REPO"

export ARISTA_LOCAL_BUILD=1 # Needed to build with local repo instead
BUILD_TYPE="MinSizeRel"
export BUILD_FBOSS_CLI=1

# DESTDIR is used also in scripts, so we need 'clean' it before run those scripts
DESTDIR_COPY=$DESTDIR
DESTDIR=""
time ./build/fbcode_builder/getdeps.py build --allow-system-packages \
   --scratch-path "$SCRATCH_DIR" fboss --extra-cmake-defines="{\"CMAKE_BUILD_TYPE\": \"$BUILD_TYPE\"}"

cd $FBOSS_REPO
./fboss/oss/scripts/package-fboss.py --scratch-path "$SCRATCH_DIR"

DESTDIR=$DESTDIR_COPY

# Check if any dynamic libraries are missing in the output directory and copy them over.
fboss_output_dir=$(find $SCRATCH_DIR -maxdepth 1 -name "fboss_bins*")
mkdir -p "$fboss_output_dir/lib64"
ld_lib_path="$LD_LIBRARY_PATH:$fboss_output_dir/lib:$fboss_output_dir/lib64"
sai_test=$(find $fboss_output_dir -name "sai_test-sai_impl*")
missing_libs=$(LD_LIBRARY_PATH="$ld_lib_path" ldd "$sai_test" | awk '/not found/{print $1}')
for lib in $missing_libs
do
   lib_path=$(find "$SCRATCH_DIR/installed" -name $lib)
   echo "Copying $lib from $lib_path to $fboss_output_dir/lib64"
   cp -L $lib_path $fboss_output_dir/lib64
done

# Verify that no more libs are missing
missing_libs=$(LD_LIBRARY_PATH="$ld_lib_path" ldd "$sai_test" | awk '/not found/{print $1}')
if ! [ -z "$missing_libs" ];
then
   echo "Test executables still missing dynamic libraries $missing_libs"
   exit 1
fi

# Also add libevent_core as there's a dependency for libevent.
lib="libevent_core-2.1.so.7"
lib_path=$(find "$SCRATCH_DIR/installed" -name $lib)
echo "Copying $lib from $lib_path to $fboss_output_dir/lib64"
cp -L $lib_path $fboss_output_dir/lib64

# Copy over kernel modules
mkdir -p "$fboss_output_dir/lib/modules"
for kernel_module in linux-kernel-bde.ko linux-user-bde.ko linux-bcm-knet.ko
do
   module_path=$(find $SAI_DIR/modules -name "$kernel_module" | head -n 1)
   echo "Copying $kernel_module from $module_path to $fboss_output_dir/lib/modules"
   cp $module_path $fboss_output_dir/lib/modules/
done

# Copy over firmware files
for fw in custom_led.bin linkscan_led_fw.bin
do
   fw_path=$(find $SAI_DIR/firmwares -name "$fw")
   echo "Copying $fw from $fw_path to $fboss_output_dir"
   cp $fw_path $fboss_output_dir
done

# Generate python thrift libraries
$SCRATCH_DIR/installed/fbthrift/bin/thrift1 -r --gen py -I $SCRATCH_DIR/repos/github.com-facebook-fboss.git -I $SCRATCH_DIR/repos/github.com-facebook-fbthrift.git/ $SCRATCH_DIR/repos/github.com-facebook-fboss.git/fboss/agent/if/ctrl.thrift
mkdir -p $fboss_output_dir/lib/fb-py-libs
cp -rf gen-py $fboss_output_dir/lib/fb-py-libs/
cp -rf $SCRATCH_DIR/installed/fbthrift/lib/fb-py-libs/thrift_py/thrift/ $fboss_output_dir/lib/fb-py-libs/
find $fboss_output_dir/lib/fb-py-libs/gen-py/ -type f  -exec sed -i '1s|^#!/usr/bin/env python$|#!/usr/bin/env python3|' {} +

echo "======= Move result to OUTPUT Dir ========"
cp -r $SCRATCH_DIR $DESTDIR
cp -r $SAI_DIR/db $DESTDIR
