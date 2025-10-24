#! /bin/bash

yum group install -y "Development Tools" --nogpgcheck
yum install -y ncurses-devel bison flex elfutils-libelf-devel openssl-devel dwarves bc rsync --nogpgcheck

# Install kernel RPMs copied from dist
for file in kernel_RPMs/*; do
   rpm -Uvh $file
done

# Install FBOSS dependencies
buildDeps=(
   elfutils-libelf-devel
   gcc
   gcc-c++
   git
   make
   python3-devel
   python3-yaml
   rpmdevtools
   wget
   epel-release
   flashrom
   lm_sensors
   i2c-tools
   usbutils
   pciutils
   libgpiod
   libgpiod-utils
   double-conversion
   xxhash-libs
   lz4
   nvme-cli
)
yum install ${buildDeps[*]} -y
