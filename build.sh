#!/bin/bash
set -e


cd "$(dirname "$0")"
# Default values
scratch_dir=/var/FBOSS/tmp_build_dir
getdeps=build/fbcode_builder/getdeps.py
build_type="MinSizeRel"
src_dir_arg=(--src-dir $PWD)
# map of sai arch-version to "<OCP SAI version> <SAI Version flag from SaiVersion.h>"
declare -A sai_map=( ["dnx-11.7"]="1.14.0 SAI_VERSION_11_7_0_0_DNX_ODP"
                     ["dnx-12.2"]="1.16.0 SAI_VERSION_12_2_0_0_DNX_ODP"
                     ["xgs-10.2"]="1.13.2 SAI_VERSION_10_2_0_0_ODP"
                     ["xgs-11.7"]="1.14.0 SAI_VERSION_11_7_0_0_ODP"
                     ["xgs-14.0"]="1.16.1 SAI_VERSION_14_0_EA_ODP" )

usage() {
   echo "Usage: $0 --sai <${!sai_map[@]}> "
   echo "          [ --scratch-dir <Scratch directory> ] "
   echo "          [ --sai-sdk-dir <Sai/Sdk directory> ] "
   echo "          [ --cmake-target <cmake_target> ] "
   echo "          [ --known-good-hash ] [ --fboss-bins-only ] "
   echo "          [ --with-debug-symbols ]  "
   echo "          [ --help ] "
}

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
      --known-good-hash)
         unset src_dir_arg
         shift
         ;;
      --fboss-bins-only)
         fboss_bins_only=1
         shift
         ;;
      --with-debug-symbols)
         build_type="Debug"
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

# Pin fboss and its dependencies to known stable commit hash
rm -rf build/deps/github_hashes
tar -xvf fboss/oss/stable_commits/latest_stable_hashes.tar.gz --no-same-owner

# Get SAI and SDK information
ocp_sai_version=$(echo $sai_info | awk '{print $1}')
sai_sdk_dir=${sai_sdk_dir:-"/saisdk-$sai_ver"}
# Copy and install SAI/SDK artifacts for fboss
fboss/oss/scripts/arista-build-helper.py $sai_sdk_dir/libsai_impl.tar.gz \
`cat $sai_sdk_dir/checksum` /tmp/sai_impl_output $ocp_sai_version
$getdeps build --scratch-path $scratch_dir sai_impl --extra-cmake-defines='{"CMAKE_CXX_STANDARD":"20"}'
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
time $getdeps build --allow-system-packages --num-jobs 20 \
   --scratch-path $scratch_dir --build-type $build_type ${src_dir_arg[@]} fboss \
   --extra-cmake-defines='{"CMAKE_CXX_STANDARD":"20"}' ${cmake_target+--cmake-target $cmake_target} \
   ${FBOSS_BARNEY_BUILD+--schedule-type continuous}
