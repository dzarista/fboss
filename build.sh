#!/bin/bash
set -e

usage() {
   echo "Usage: $0 --arch <dnx|xgs> "
   echo "          [ --kernel-dir <Kernel directory> ] "
   echo "          [ --scratch-dir <Scratch directory> ] "
   echo "          [ --sai-sdk-dir <Sai/Sdk directory> ] "
   echo "          [ --clean ] [ --known-good-hash ] "
   echo "          [ --fboss-bins-only ] [ --with-debug-symbols ] "
   echo "          [ --rebuild-fboss ] [ --help ] "
}

cd "$(dirname "$0")"
# Default values
sai_sdk_dir=/result
scratch_dir=/var/FBOSS/tmp_build_dir
kernel_dir=/kernel-6.4

while [[ $# -gt 0 ]]; do
   case $1 in
      --scratch-dir)
         scratch_dir="$2"
         shift; shift
         ;;
      --sai-sdk-dir)
         sai_sdk_dir="$2"
         shift; shift
         ;;
      --rebuild-fboss)
         clean_fboss=1
         shift
         ;;
      --clean)
         clean_fboss=1
         clean_and_exit=1
         shift
         ;;
      --fboss-bins-only)
         fboss_bins_only=1
         shift
         ;;
      --known-good-hash)
         known_good_hash=1
         shift
         ;;
      --with-debug-symbols)
         debug_symbols=1
         shift
         ;;
      --arch)
         if [[ "$2" == "dnx" || "$2" == "xgs" ]]; then
            arch="$2"
         else
            echo "Invalid architecture. Choose between: xgs dnx"; exit 1
         fi
         shift; shift
         ;;
      --kernel-dir)
         kernel_dir="$2"
         shift; shift
         ;;
      --help)
         usage; exit 0
         shift
         ;;
      *)
         echo "Unknown option "$1""; exit 1
         ;;
  esac
done

# Clean FBOSS
if ! [[ -z $clean_fboss ]]; then
   echo "==== Clean up FBOSS build artifacts ===="
   make -C $kernel_dir M=~+/fboss.bsp.arista/bsp-kmods clean
   make -C fboss.bsp.arista/showtech clean
   make -C arista/psu-upgrade clean
   rm -rf $scratch_dir
   if ! [[ -z $clean_and_exit ]]; then exit 0; fi
fi

if [ -z "$arch" ]; then
   echo "Choose an architecture with --arch"; usage; exit 1
fi

echo "==== Running build with arch=$arch and kernel from $kernel_dir ===="
set -x

# In case we only want to rebuild fboss, run cmake from build dir and exit
if ! [ -z $fboss_bins_only ]; then
   $scratch_dir/build/fboss/run_cmake.py --install
   exit 0
fi

# Override the default sai versions and type for xgs
if [ $arch == "xgs" ]; then
   ocp_sai_version="1.13.2"
   export SAI_SDK_VERSION="SAI_VERSION_10_2_0_0_ODP"
fi

if [ -z $known_good_hash ]; then
   src_dir_arg=(--src-dir $PWD)
fi

build_type="Debug"
if [ -z $debug_symbols ]; then
   build_type="MinSizeRel"   
fi

# workaround for barney
touch ".git"

# Pin fboss and its dependencies to known stable commit hash
rm -rf build/deps/github_hashes
tar -xvf fboss/oss/stable_commits/latest_stable_hashes.tar.gz --no-same-owner
sed -i '/dependencies/asai_impl' build/fbcode_builder/manifests/fboss

sai_install_dir() { 
   ./build/fbcode_builder/getdeps.py show-inst-dir --scratch-path $scratch_dir fboss \
      --extra-cmake-defines='{"CMAKE_CXX_STANDARD":"20"}' --recursive  | grep sai_impl-
}

sai_checksum() { 
   echo `find $sai_sdk_dir/include $sai_sdk_dir/libraries/ -type f -print0 | \
      sort -z | xargs -0 xxh128sum` $arch | xxh128sum 
}

# Provide brcm sai static library
if [[ $(cat $scratch_dir/.sai_hash) = `sai_checksum` ]] && [[ -f $scratch_dir/.libsai.copy ]] && \
   [[ -f build/fbcode_builder/manifests/sai_impl ]] && [[ -d `sai_install_dir` ]]; then
   cp $scratch_dir/.libsai.copy build/fbcode_builder/manifests/libsai
else
   fboss/oss/scripts/build-helper.py $sai_sdk_dir/libraries/libsai_impl.a \
      $sai_sdk_dir/include/ /tmp/sai_impl_output $ocp_sai_version
   mkdir -p $scratch_dir; echo "`sai_checksum`" > $scratch_dir/.sai_hash
   cp build/fbcode_builder/manifests/libsai $scratch_dir/.libsai.copy
fi

# Setup environment for FBOSS build
export SAI_ONLY=1
export SAI_BRCM_IMPL=1 # Needed only for BRCM SAI
export GETDEPS_USE_WGET=1
export BUILD_FBOSS_CLI=1
export IS_OSS=1
unset DESTDIR

echo "==== Building fboss ===="
time ./build/fbcode_builder/getdeps.py build --allow-system-packages --num-jobs 40 \
   --scratch-path $scratch_dir --build-type $build_type ${src_dir_arg[@]} fboss \
   --extra-cmake-defines='{"CMAKE_CXX_STANDARD":"20"}'

echo "==== Building bsp-kmods ===="
make -C $kernel_dir M=~+/fboss.bsp.arista/bsp-kmods modules

echo "==== Building showtech ===="
make -C fboss.bsp.arista/showtech

echo "==== Building psu-upgrade ===="
make -C arista/psu-upgrade

echo "==== Generating python thrift libraries ===="
thrift_files=( 
   fboss/agent/if/ctrl.thrift
   fboss/agent/if/hw_ctrl.thrift
   fboss/qsfp_service/if/qsfp.thrift
   fboss/platform/fan_service/if/fan_service.thrift
   fboss/platform/rackmon/if/rackmonsvc.thrift
   fboss/platform/sensor_service/if/sensor_service.thrift
)
for thrift_file in ${thrift_files[@]}; do
   $scratch_dir/installed/fbthrift/bin/thrift1 -r --gen py -o $scratch_dir -I $PWD \
      -I $scratch_dir/repos/github.com-facebook-fbthrift.git $thrift_file
done

echo "==== Extracting platform mappings ===="
src_mapping_dir="fboss/agent/platforms/common"
src_mapping_files=(
    $src_mapping_dir/meru800bia/Meru800biaPlatformMapping.cpp
    $src_mapping_dir/meru800bfa/Meru800bfaP2PlatformMapping.h
    $src_mapping_dir/meru800bfa/Meru800bfaProdPlatformMapping.h
    $src_mapping_dir/meru800bfa/Meru800bfaP1PlatformMapping.cpp
    $src_mapping_dir/darwin/DarwinPlatformMapping.cpp
)
arista/build-utils/ExtractMappings.py -d $scratch_dir/PlatformMappings ${src_mapping_files[@]}
