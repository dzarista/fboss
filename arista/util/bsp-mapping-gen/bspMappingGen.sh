#!/bin/bash
echo "Running bspMappingGen - requires a prior successful build using fbossctl"

FBOSS_DIR="/var/FBOSS"
SCRATCH_DIR="$FBOSS_DIR/tmp_build_dir"
fboss_output_dir=$(find $SCRATCH_DIR -maxdepth 1 -name "fboss_bins*")

BSPMAPPING_GEN="$fboss_output_dir/bin/fboss-bspmapping-gen"

if [ ! -e "$BSPMAPPING_GEN" ]; then
    echo "$BSPMAPPING_GEN doesn't exist. A prior successful build is required."
    exit 1
fi

# Install dependencies
echo "Installing dependencies"
dnf install -y double-conversion-devel xxhash-devel

# Copy fboss-bspbapping-gen executable to the working directory of the Meta script
mkdir -p /tmp/fbcode_builder_getdeps-ZvarZFBOSSZfboss.gitZbuildZfbcode_builder-root/build/fboss
cp "$BSPMAPPING_GEN" /tmp/fbcode_builder_getdeps-ZvarZFBOSSZfboss.gitZbuildZfbcode_builder-root/build/fboss

# Meta's helper script needs to be run from the root of the FBOSS repository.
cd /var/FBOSS/fboss.git
./fboss/lib/bsp/bspmapping/run-helper.sh

mkdir -p $FBOSS_DIR/fboss.git/tmp/generated_bsp_mappings
cp -rf /tmp/generated_configs $FBOSS_DIR/fboss.git/tmp/generated_bsp_mappings

echo "Mapping files generated successfully"
echo "See configs located under tmp/generated_bsp_mappings"