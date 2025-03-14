#!/bin/bash

set -e

arch=$1
kernel=$2
DESTDIR=${DESTDIR:-"/src/dest"}

fboss_spec_dir=arista/rpm
built_rpms_dir="/tmp/rpmbuild/RPMS/x86_64"
fboss_ptest_data_dir="${DESTDIR}/usr/share/ptest-data/Fboss"
rpm_dest="$fboss_ptest_data_dir/RPMS/$arch/$kernel"

mkdir -p /tmp/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS,BUILDROOT}
mkdir -p $rpm_dest
mkdir -p /tmp/fboss.git
# Copy arista dir from arista-fboss for rpmbuild to find
cp -r arista /tmp/fboss.git

# Avoid packaging kmods for kernel versions 4.18 and 5.12
if [ "$kernel" == "4.18" ] || [ "$kernel" == "5.12" ]; then
   filter="-not -name *arista_bsp_kmods.spec"
fi
# Find RPM spec files
RPMS=($(find ~+/$fboss_spec_dir -type f -name *.spec $filter))

# Build RPMs
pushd /tmp
for rpm in "${RPMS[@]}"; do
    rpmbuild -v --define '_topdir /tmp/rpmbuild' -bb "${rpm}" --root /tmp --define 'root /tmp'
    built_rpm=$(find "${built_rpms_dir}" -type f -name "$(basename ${rpm%.*})-*")
    cp -f "${built_rpm}" "${rpm_dest}"
done
echo "FBOSS RPMs are copied to $rpm_dest"
popd

# Copy platform mappings
cp -rf /tmp/tmp_build_dir/PlatformMappings ${fboss_ptest_data_dir}/

# Copy swi modules
cp -rf swi-modules ${fboss_ptest_data_dir}/
