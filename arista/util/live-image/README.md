# CentOS live image creation tool

## Usage
create_live_image.sh <kernel version> <centos major release>.
Pass the kernel version and CentOS major release version used for building the live image as arguments.

## Description
The scripts are written based on the steps in aid/11233. The kernel version and CentOS stream used for building the live image are passed as arguments to the high level script create_live_image.sh.

create_live_image.sh runs docker_script.sh with the logic to create the live image inside a CentOS container.
The live image is created from a chroot environment with minimal installation of the given CentOS stream. The kernel RPMs corresponding to the given kernel version are installed in the chroot environment after downloading them from /dist/storage/fboss/kernel/.

The live image will be present as a .tar file under build_dir/build/.

# Kernel source tarball creation tool

## Usage
create_kernel_source_tarball.sh <kernel_version>
Pass the kernel version used for creating the source tarball.

## Description
In addition to a creating a live image, we must publish a tarball containing kernel source headers so that external kernel RPMs can be built against this version of the Linux kernel. This script creates that tarball, which should then be published to https://dist.aristanetworks.com/storage/fboss/fbossImageFiles/.

The created tarball will be present as a .tar.gz file under src_tar_build_dir/.
