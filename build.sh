#!/bin/bash

set -e

FBOSS_DIR=/tmp
FBOSS_REPO=$SRCDIR_0
KERNEL=$1
SAI_DIR=/src/dest/result
SCRATCH_DIR="$FBOSS_DIR/tmp_build_dir"

if [ $KERNEL = "4.18" ]; then
   export KERNEL_SRC="4.18.0-408.el8.x86_64"
elif [ $KERNEL = "5.12" ]; then
   export KERNEL_SRC="5.12.0-0_fbk2_3390_g7ecb4ac46d7f"
elif [ $KERNEL = "6.4" ]; then
   export KERNEL_SRC="6.4.3-0_fbk747_rc2_1199_ga95cd85c72c4"
else
   export KERNEL_SRC="5.19.0"
fi

CENTOS_RELEASE_MAJOR=$(grep -o "[^ ]*$" /etc/centos-release | cut -d '.' -f 1)
echo "Build iamge base centos version : el$CENTOS_RELEASE_MAJOR"

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
# Set the required build env vars for Centos 9
if [ "$CENTOS_RELEASE_MAJOR" = "9" ]; then
   export IS_OSS=1
   export IS_OSS_FBOSS_CENTOS9=1
   REPO_PREFIX="$SCRATCH_DIR/repos/github.com-facebook"
   # Fetch fbthrift and folly and update the C++ standard to v20. C++20 is
   # required for building coroutine support into folly and fbthrift.
   for fboss_dep in folly fbthrift
   do
      ./build/fbcode_builder/getdeps.py --scratch-path "$SCRATCH_DIR" fetch $fboss_dep
      sed -i 's/STANDARD 17/STANDARD 20/g' "$REPO_PREFIX-$fboss_dep.git/CMakeLists.txt"
   done
fi

time ./build/fbcode_builder/getdeps.py build --allow-system-packages --num-jobs 20 \
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

if [ "$KERNEL" == "5.19" ] || [ "$KERNEL" == "6.4" ]; then
   # Download fboss kernel src
   KERNEL_SRC_TAR=FBOSS_KERNEL_SRC_"${KERNEL_SRC}".tar.gz
   wget -P $SCRATCH_DIR/downloads http://dist/storage/fboss/fbossImageFiles/"${KERNEL_SRC_TAR}"
   tar -xf $SCRATCH_DIR/downloads/"${KERNEL_SRC_TAR}" -C $SCRATCH_DIR/installed

   # Building bsp-kmods
   make -C $SCRATCH_DIR/installed/$KERNEL_SRC M=$FBOSS_REPO/arista/bsp-kmods modules
   mkdir -p $SCRATCH_DIR/bsp-kmods
   cp -f $FBOSS_REPO/arista/bsp-kmods/*.ko $SCRATCH_DIR/bsp-kmods/
fi

# Building showtech dependencies
make -C $FBOSS_REPO/arista/showtech
mkdir -p $SCRATCH_DIR/showtech
cp -f $FBOSS_REPO/arista/showtech/platform-showtech $SCRATCH_DIR/showtech/

# Generate python thrift libraries
$SCRATCH_DIR/installed/fbthrift/bin/thrift1 -r --gen py -I $SCRATCH_DIR/repos/github.com-facebook-fboss.git -I $SCRATCH_DIR/repos/github.com-facebook-fbthrift.git/ $SCRATCH_DIR/repos/github.com-facebook-fboss.git/fboss/agent/if/ctrl.thrift
mkdir -p $fboss_output_dir/lib/fb-py-libs
cp -rf gen-py $fboss_output_dir/lib/fb-py-libs/
cp -rf $SCRATCH_DIR/installed/fbthrift/lib/fb-py-libs/thrift_py/thrift/ $fboss_output_dir/lib/fb-py-libs/
find $fboss_output_dir/lib/fb-py-libs/gen-py/ -type f  -exec sed -i '1s|^#!/usr/bin/env python$|#!/usr/bin/env python3|' {} +

# Cache the fboss commit that we built, this will be packaged and available on the
# box at /opt/fboss/ when arista-fboss-core RPM is installed.
# Since we are always doing a local build in barney, we can just use the commit hash
# the source repo is checked out at, barney maps this to $SRC_0
echo "$SRC_0" > $fboss_output_dir/arista-fboss-version

echo "======= Move result to OUTPUT Dir ========"
cp -r $SCRATCH_DIR $DESTDIR
cp -r $SAI_DIR/db $DESTDIR
