#!/bin/bash
usage() {
   echo "Usage: $0 "
   echo "  [ --scratch-dir <Scratch directory> ] "
   echo "  [ --sai-sdk-dir <Sai/Sdk directory> ] "
   echo "  [ --export-dir  <RPM export dir> ] "
   echo "  [ --compress ] [ --help ] "
}

cd "$(dirname "$0")"
# Spec files location
fboss_spec_dir=arista/rpm
# Default values
scratch_dir=/var/FBOSS/tmp_build_dir
sai_sdk_dir=/result
export_dir=/src/dest/
compression_level=1

args=()
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
      --export-dir)
         export_dir="$2"
         shift; shift
         ;;
      --compress)
         compression_level=9
         shift
         ;;
      --help)
         usage; exit 0
         shift
         ;;
      -*|--*)
         echo "Unknown option $1"; exit 1
         ;;
      *)
         args+=("$1")
         shift
         ;;
   esac
done

set -ex

# Clear old fboss_bins-* dir and package
rm -rf "$scratch_dir"/fboss_bins-1*
fboss/oss/scripts/package-fboss.py --scratch-path "$scratch_dir"
fboss_out_dir=$(find "$scratch_dir" -maxdepth 1 -name fboss_bins-1*)

# Store the commit we built for it to be available in /opt/fboss/arista-fboss-version
if [[ -z "$SRC_0" ]]; then
   fboss_commit=$(git -c safe.directory=$PWD rev-parse HEAD)
   echo "arista-fboss@$fboss_commit" > $fboss_output_dir/arista-fboss-version
else
   echo "$SRC_0" > $fboss_out_dir/arista-fboss-version
fi

# Get RPM specs from either the command line or all from arista/rpm
if [[ ${#args[@]} -lt 1 ]]; then
   rpms=$fboss_spec_dir/*
else
   rpms="${args[@]/#/$fboss_spec_dir/}"
fi

# Build RPMs
export QA_SKIP_RPATHS=1 # Needed to skip rpath check
for rpm in $rpms; do
   rpmbuild -v --define '_topdir /tmp/rpmbuild' --define "_fboss_dir $PWD" \
      --define "_sai_sdk_dir $sai_sdk_dir" --define "_scratch_dir $scratch_dir" \
      --define "_tmppath /tmp" --define "_binary_payload w$compression_level.zstdio" \
      --undefine __brp_mangle_shebangs -bb $rpm
done

# Move built RPMS
mkdir -p "$export_dir"/RPMS
mv /tmp/rpmbuild/RPMS/x86_64/* "$export_dir"/RPMS/

# Copy platform mappings
cp -rf "$scratch_dir"/PlatformMappings "$export_dir"

# Copy swi modules
cp -rf swi-modules "$export_dir"
