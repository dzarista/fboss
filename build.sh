#!/bin/bash
set -e

usage() {
   echo "Usage: $0 --sai <dnx-11.7|xgs-10.2|dnx-12.2> "
   echo "          [ --kernel-dir <Kernel directory> ] "
   echo "          [ --scratch-dir <Scratch directory> ] "
   echo "          [ --sai-sdk-dir <Sai/Sdk directory> ] "
   echo "          [ --clean ] [ --known-good-hash ] "
   echo "          [ --fboss-bins-only ] [ --bsp-kmods-only ] "
   echo "          [ --with-debug-symbols ] [ --rebuild-fboss ] "
   echo "          [ --cmake-target ][ --help ] "
}

cd "$(dirname "$0")"
# Default values
scratch_dir=/var/FBOSS/tmp_build_dir
kernel_dir=/kernel-6.4
getdeps=build/fbcode_builder/getdeps.py
# map of sai arch-version to "<OCP SAI version> <SAI Version flag from SaiVersion.h>"
declare -A sai_map=( ["dnx-11.7"]="1.14.0 SAI_VERSION_11_7_0_0_DNX_ODP"
                     ["dnx-12.2"]="1.16.0 SAI_VERSION_12_2_0_0_DNX_ODP"
                     ["xgs-10.2"]="1.13.2 SAI_VERSION_10_2_0_0_ODP"
                     ["xgs-11.7"]="1.14.0 SAI_VERSION_11_7_0_0_ODP"
                     ["xgs-14.0"]="1.16.1 SAI_VERSION_14_0_EA_ODP" )

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
      --bsp-kmods-only)
         bsp_kmods_only=1
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
      --sai)
         sai_ver=${2:-None}
         sai_info=${sai_map["$sai_ver"]}
         if [ -z "$sai_info" ]; then
            echo "Invalid SAI architecture/version. Choose between: ${!sai_map[@]}"; exit 1
         fi
         shift; shift
         ;;
      --kernel-dir)
         kernel_dir="$2"
         shift; shift
         ;;
      --cmake-target)
         cmake_target="$2"
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

build_bsp_kmods() {
   echo "==== Building bsp-kmods ===="
   make -C $kernel_dir M=~+/fboss.bsp.arista/bsp-kmods modules
}

# Clean FBOSS
if ! [[ -z $clean_fboss ]]; then
   echo "==== Clean up FBOSS build artifacts ===="
   make -C $kernel_dir M=~+/fboss.bsp.arista/bsp-kmods clean
   make -C fboss.bsp.arista/showtech clean
   make -C arista/psu-upgrade clean
   $getdeps clean --scratch-path $scratch_dir
   if ! [[ -z $clean_and_exit ]]; then exit 0; fi
fi

if [ -z "$sai_ver" ]; then
   echo "Choose a SAI version/architecture with --sai"; usage; exit 1
fi

echo "==== Running build with arch=$arch and kernel from $kernel_dir ===="
set -x

# In case we only want to rebuild fboss, run cmake from build dir and exit
if ! [ -z $fboss_bins_only ]; then
   $scratch_dir/build/fboss/run_cmake.py --install
   exit 0
fi

if ! [ -z $bsp_kmods_only ]; then
   build_bsp_kmods
   exit 0
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

# Copy and install SAI/SDK artifacts for fboss
ocp_sai_version=$(echo $sai_info | awk '{print $1}')
sai_sdk_dir=${sai_sdk_dir:-"/saisdk-$sai_ver"}
fboss/oss/scripts/arista-build-helper.py $sai_sdk_dir/libsai_impl.tar.gz \
   `cat $sai_sdk_dir/checksum` /tmp/sai_impl_output $ocp_sai_version
$getdeps build --scratch-path $scratch_dir sai_impl \
   --extra-cmake-defines='{"CMAKE_CXX_STANDARD":"20"}'
echo $sai_sdk_dir > $scratch_dir/.saisdkdir

# Setup environment for FBOSS build
export SAI_ONLY=1
export SAI_BRCM_IMPL=1 # Needed only for BRCM SAI
export GETDEPS_USE_WGET=1
export BUILD_FBOSS_CLI=1
export IS_OSS=1
export SAI_SDK_VERSION=$(echo $sai_info | awk '{print $2}')
export SAI_VERSION=$ocp_sai_version
unset DESTDIR
# Configure ccache for compiler level caching
export CCACHE_CONFIGPATH=$(realpath arista/build-utils/ccache.conf)

echo "==== Building fboss ===="
time $getdeps build --allow-system-packages --num-jobs 40 \
   --scratch-path $scratch_dir --build-type $build_type ${src_dir_arg[@]} fboss \
   --extra-cmake-defines='{"CMAKE_CXX_STANDARD":"20"}' ${cmake_target+--cmake-target $cmake_target} \
   ${FBOSS_BARNEY_BUILD+--schedule-type continuous}

build_bsp_kmods

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
    $src_mapping_dir/glath05a-64o/Glath05a-64oPlatformMapping.cpp
)
arista/build-utils/ExtractMappings.py -d $scratch_dir/PlatformMappings ${src_mapping_files[@]}
