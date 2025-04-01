#! /bin/bash

usage() {
   echo "Pass the kernel version and CentOS major release version used for building the live image as arguments"
   echo "usage: $0 <kernel version> <centos stream number>"
}

if [[ $# -lt 2 ]]; then
    usage
    exit 1
fi

kernel_version=$1
centos_stream_number=$2

build_dir_path=$(pwd)/build_dir
# Clean up build_dir if it already exists. This is where the live image related files will be stored
sudo rm -rf $build_dir_path
# Set up build_dir and update permissions to mount it in docker container
mkdir $build_dir_path
chmod -R a+rw $build_dir_path
# Script to be run from the docker container
cp docker_script.sh $build_dir_path
# Script to be run from the chroot environment created in the container
cp installation_script.sh $build_dir_path
# Copy kernel RPMs from dist to build_dir
mkdir $build_dir_path/kernel_RPMs
a4 scp dist:/dist/storage/fboss/kernel/kernel*-$kernel_version*.rpm $build_dir_path/kernel_RPMs

docker_image=quay.io/centos/centos:stream$centos_stream_number
docker run -ti --rm --mount type=bind,source=/b5/container/$(hostname)/rootfs/data/${build_dir_path},target=/app $docker_image /app/docker_script.sh $kernel_version $centos_stream_number
