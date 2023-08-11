#!/bin/bash

# Add /usr/local/bin, for doxygen.
export PATH="$PATH:/usr/local/bin"

if [ -f /.dockerenv ]; then
   echo "running in a container - assuming /var/FBOSS base"
   FBOSS_DIR="/var/FBOSS"
else
   echo "Running outside of container. Using $FBOSS_DIR"
   if ! [ -d "$FBOSS_DIR" ];
   then
      echo "Invalid FBOSS_DIR, provide a valid directory path."
      exit 1
   fi
   FBOSS_DIR="$(realpath $FBOSS_DIR)"
fi

usage() {
   echo "Usage: $1 --arch <dnx|xgs> --kernel <4.18|5.12> "
   echo "          [ --build-dir <build directory> ] "
   echo "          [ --rebuild-all ] [ --rebuild-fboss ] "
   echo "          [ --fboss-bins-only ]"
   exit 1
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --build-dir)
      FBOSS_DIR=$2
      shift
      shift
      ;;
    --rebuild-all)
      REBUILD_SDK=TRUE
      REBUILD_FBOSS=TRUE
      shift
      ;;
    --rebuild-fboss)
      REBUILD_FBOSS=TRUE
      shift
      ;;
    --fboss-bins-only)
      FBOSS_BINS_ONLY=TRUE
      shift
      ;;
    --known-good-hash)
      BUILD_KNOWN_GOOD_HASH=TRUE
      shift
      ;;
    --arch)
      if [ "$2" == "dnx" ];
      then
         ARCH="dnx"
      elif [ "$2" == "xgs" ];
      then
         ARCH="xgs"
      else
         echo "Invalid architecture $2, please provide one of xgs or dnx."
	 exit 1
      fi
      shift
      shift
      ;;
    --kernel)
      if [ "$2" == "4.18" ];
      then
         KERNEL="4.18"
      elif [ "$2" == "5.12" ];
      then
         KERNEL="5.12"
      else
         echo "Unsupported kernel $2, please provide one of 4.18 or 5.12."
	 exit 1
      fi
      shift
      shift
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift
      ;;
  esac
done

if [ -z "$ARCH" ]; then
   usage
fi

set -ex
echo "================= Running build with $FBOSS_DIR and ARCH=$ARCH and KERNEL=$KERNEL"

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

if [ $KERNEL == "4.18" ];
then
   export KERNEL_SRC="$FBOSS_DIR/4.18.0-408.el8.x86_64"
else
   export KERNEL_SRC="$FBOSS_DIR/5.12.0-0_fbk2_3390_g7ecb4ac46d7f"
fi

# install missing dependencies for SDK build.
dnf install -y sudo
sudo dnf install --enablerepo powertools -y perl-List-MoreUtils perl-YAML.noarch \
   perl-Data-Compare perl-Moose perl-MooseX-Role* perl-Clone libyaml-devel
sudo dnf install -y python3-filelock platform-python-devel

# Setup unversioned-python aliased to python3
alternatives --set python /usr/bin/python3
# Install python3 module dependencies
pip3 install GitPython

SAI_DIR="$FBOSS_DIR/Aqua_SAI/"
if [ $ARCH == "dnx" ];
then
   SAI_BUILD_DIR="$SAI_DIR/output/x86-dnx-deb-static-fboss"
else
   SAI_BUILD_DIR="$SAI_DIR/output/x86-xgsall-deb-static-fboss"
fi

# Delete SDK var in the env. It can cause the SDK build to fail.
export SDK=""
cd $SAI_BUILD_DIR
export KERNDIR="$KERNEL_SRC"
export BCM_KERNEL_MODULES_DIR="$SAI_DIR/sdk-src/hsdk_6.5.28_SAI_10.0.0_EA/$ARCH-sdk-6.5.28-gpl-modules"
echo "****REBUILD_SDK $REBUILD_SDK"
if ! [ -z "$REBUILD_SDK" ];
then
   echo "======== Clean up Broadcom SDK build artifacts ========"
   time make clean -j 16
   for dir in $(ls $SAI_BUILD_DIR)
   do
      if [ -d $SAI_BUILD_DIR/$dir ];
      then
         rm -r "$SAI_BUILD_DIR/$dir"
      fi
   done

   cd $BCM_KERNEL_MODULES_DIR
   make -C systems/linux/user/common/ platform=x86-smp_generic_64-2_6 \
      kernel_version=2_6 LINUX_UAPI_SPLIT=1 clean

   echo "======= Starting Broadcom SDK build ========"
   cd $SAI_BUILD_DIR
   time make -j 16
   cd $BCM_KERNEL_MODULES_DIR
   export SDK=$PWD
   make -C systems/linux/user/common/ platform=x86-smp_generic_64-2_6 \
      kernel_version=2_6 LINUX_UAPI_SPLIT=1 kernel_modules
else
   export SDK=$BCM_KERNEL_MODULES_DIR
fi

# Instructions from
# https://github.com/facebook/fboss/blob/main/installer/howto/Building_FBOSS_on_containers.md
# With some changes to avoid overwriting git repos etc.
SCRATCH_DIR="$FBOSS_DIR/tmp_build_dir"
cd $FBOSS_DIR/
if ! [ -d fboss.git ];
then
   git clone https://github.com/facebook/fboss fboss.git
fi

# Cleanup fboss build artefacts with --rebuild-fboss
echo "****REBUILD_FBOSS $REBUILD_FBOSS"
if ! [ -z "$REBUILD_FBOSS" ];
then
   echo "======== Clean up FBOSS build artifacts ========"
   rm -rf $SCRATCH_DIR/build # remove existing build dir if any
   rm -rf $SCRATCH_DIR/installed
   rm -rf $SCRATCH_DIR/extracted
   rm -rf $SCRATCH_DIR/repos
   rm -rf "$SCRATCH_DIR"/fboss_bins*
fi
cd $FBOSS_DIR/fboss.git

# Optionally, pin the fboss and its dependencies to known
# stable commit hash
rm -rf build/deps/github_hashes/facebook
rm -rf build/deps/github_hashes/facebookincubator
tar -xvf fboss/oss/stable_commits/latest_stable_hashes.tar.gz

echo "======= Starting FBOSS build ========"

# Install dependencies for FBOSS build
bash $FBOSS_DIR/fboss.git/installer/centos-8-x64_64/install-tools.sh

# Prepare FBOSS Build
echo "****FBOSS_BINS_ONLY $FBOSS_BINS_ONLY"
if ! [ -z "$FBOSS_BINS_ONLY" ];
then
   # Only re-run cmake
   cd $SCRATCH_DIR/build/fboss
   ./run_cmake.py --install
else
   rm -rf $FBOSS_DIR/built-sai
   mkdir -p $FBOSS_DIR/built-sai/experimental
   mkdir -p $FBOSS_DIR/built-bcm-sai
   cp $SAI_BUILD_DIR/libraries/libsai.a $FBOSS_DIR/built-bcm-sai/libsai_impl.a
   cp $SAI_DIR/include/experimental/*.* $FBOSS_DIR/built-sai/experimental
   cd $FBOSS_DIR/fboss.git/fboss/oss/scripts
   ./build-helper.py $FBOSS_DIR/built-bcm-sai/libsai_impl.a \
      $FBOSS_DIR/built-sai/experimental/ $FBOSS_DIR/sai_impl_output

   # Build FBOSS
   export SAI_ONLY=1
   export SAI_BRCM_IMPL=1 # Needed only for BRCM SAI
   export GETDEPS_USE_WGET=1
   cd "$FBOSS_DIR/fboss.git"

   echo "****BUILD_KNOWN_GOOD_HASH $BUILD_KNOWN_GOOD_HASH"
   if [ -z "$BUILD_KNOWN_GOOD_HASH" ]; then
      export ARISTA_LOCAL_BUILD=1 # Needed to build with local repo instead
   fi
   time ./build/fbcode_builder/getdeps.py build --allow-system-packages \
      --scratch-path "$SCRATCH_DIR" fboss --extra-cmake-defines='{"CMAKE_BUILD_TYPE": "MinSizeRel"}'
   cd $FBOSS_DIR/fboss.git
   ./fboss/oss/scripts/package-fboss.py --scratch-path "$SCRATCH_DIR"

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
      module_path=$(find $BCM_KERNEL_MODULES_DIR -name "$kernel_module" | head -n 1)
      echo "Copying $kernel_module from $module_path to $fboss_output_dir/lib/modules"
      cp $module_path $fboss_output_dir/lib/modules/
   done

   # Copy over firmware files
   for fw in custom_led.bin linkscan_led_fw.bin
   do
      fw_path=$(find $FBOSS_DIR -name "$fw")
      echo "Copying $fw from $fw_path to $fboss_output_dir"
      cp $fw_path $fboss_output_dir
   done
fi

set +ex
