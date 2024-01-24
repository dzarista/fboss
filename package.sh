#!/bin/bash

set -e

FBOSS_REPO=$(pwd)

FBOSS_REPO_RPM_DIR="$FBOSS_REPO/arista/rpm"
FBOSS_RPM_DIR="/tmp/artifacts/"
RPM_DIR="/tmp/rpmbuild/RPMS/x86_64"
RPMS=()

mkdir -p /tmp/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS,BUILDROOT}
echo "FBOSS_RPM_DIR $FBOSS_RPM_DIR"
mkdir -p $FBOSS_RPM_DIR

mkdir -p fboss.git
cp -r arista fboss.git
cp -r /src/dest/tmp_build_dir .

# Find the RPMs to build.
RPMS=($(find "${FBOSS_REPO_RPM_DIR}" -type f -name *.spec))

mkdir -p $FBOSS_REPO/Aqua_SAI/sdk-src/tools/sand
cp -r /src/dest/db $FBOSS_REPO/Aqua_SAI/sdk-src/tools/sand

for rpm in "${RPMS[@]}"; do
    rpmbuild -v --define '_topdir /tmp/rpmbuild' -bb "${rpm}" --root /tmp --define 'root /tmp'
    built_rpm=$(find "${RPM_DIR}" -type f -name "$(basename ${rpm%.*})*")
    cp -f "${built_rpm}" "${FBOSS_RPM_DIR}"
done

# upload created RPMS to artifactory
ARCH=$1
KERNEL=$2
export COMMITID=$(echo $SRC_0 | awk -F '#' '{print substr($2, 1, 7)}')
find /tmp/artifacts -type f -exec basename {} \; | sort | xargs -I{} curl -T /tmp/artifacts/{} https://artifactory.infra.corp.arista.io/artifactory/arista-fboss/jenkins/builds/$COMMITID/fbossOssRpms/$ARCH/$KERNEL/{}

# create yaml file with commitid which allow find related url to artifactory:
# http://artifactory.infra.corp.arista.io/ui/native/arista-fboss/jenkins/builds/$COMMITID/fbossOssRpms/$ARCH/$KERNEL
mkdir -p $DESTDIR/artifacts/
echo $COMMITID > $DESTDIR/artifacts/fboss.yaml
