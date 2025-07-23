#! /bin/bash

# script to test FBOSS live image creation tool
# usage: test_live_image_creation.sh <kernel version> <centos release version> <MUT container name>
# note: the DUT to sanitize the live image with must already be grabbed in the MUT container

kernel_version=$1
centos_release_version=$2
container_name=$3
script_dir=$(dirname "$0")

${script_dir}/../create_live_image.sh $kernel_version $centos_release_version
live_image_file_name=centos${centos_release_version}_${kernel_version}_live.tar
a scp ${script_dir}/../build_dir/build/${live_image_file_name} dist:/dist/storage/fboss/fboss_live_image_test.tar

helper_script_name=test_live_image_creation_container_action.sh
cp ${script_dir}/${helper_script_name} ~/.
a4c shell $container_name ~/${helper_script_name}
