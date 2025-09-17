#! /bin/bash

# Simple script for extracting kernel headers from the kernel-devel RPM and
# packaging them into a tarball that can be used to build external kernel
# modules.

usage() {
   echo "Pass the kernel version of the source tarball to create"
   echo "usage: $0 <kernel version>"
}

if [[ $# -lt 1 ]]; then
    usage
    exit 1
fi

kernel_version=$1

# Prepare build directory
build_dir_path=$(pwd)/src_tar_build_dir
sudo rm -rf $build_dir_path
mkdir -p $build_dir_path
chmod -R a+rw $build_dir_path

# Download the kernel-devel RPM
rpm_dir_path=$build_dir_path/RPM
mkdir -p $rpm_dir_path
echo "Downloading kernel-devel RPM from dist"
a4 scp dist:/dist/storage/fboss/kernel/kernel-devel-$kernel_version*.rpm $rpm_dir_path
kernel_devel_rpm=$(find $rpm_dir_path -type f -name "kernel-devel-*.rpm")
if [ -z "$kernel_devel_rpm" ]; then
    echo "Failed to download kernel-devel RPM for kernel version $kernel_version"
    exit 1
fi

# Extract the kernel source from the RPM and create a tarball
tarball_dir_path=$build_dir_path/tarball
mkdir -p $tarball_dir_path
cd $tarball_dir_path
echo "Extracting RPM contents to $tarball_dir_path"
rpm2cpio $kernel_devel_rpm | cpio -idm

kernel_src_dir_path=$tarball_dir_path/usr/src/kernels
if [ -z "$kernel_src_dir_path" ]; then
   echo "Kernel source directory $kernel_src_dir_path not found"
   exit 1
fi

cd $kernel_src_dir_path
tarball=FBOSS_KERNEL_SRC_$kernel_version.tar.gz
tar -cf $tarball $kernel_version/
mv $tarball $build_dir_path/
echo "Created kernel source tarball: $build_dir_path/$tarball"

