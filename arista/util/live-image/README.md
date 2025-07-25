# CentOS live image creation tool

## Usage
create_live_image.sh <kernel version> <centos major release>.
Pass the kernel version and CentOS major release version used for building the live image as arguments.

## Description
The scripts are written based on the steps in aid/11233. The kernel version and CentOS stream used for building the live image are passed as arguments to the high level script create_live_image.sh.

create_live_image.sh runs docker_script.sh with the logic to create the live image inside a CentOS container.
The live image is created from a chroot environment with minimal installation of the given CentOS stream. The kernel RPMs corresponding to the given kernel version are installed in the chroot environment after downloading them from /dist/storage/fboss/kernel/.

The live image will be present as a .tar file under build_dir/build/.
