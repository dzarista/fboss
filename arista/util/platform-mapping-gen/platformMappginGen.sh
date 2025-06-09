#!/bin/bash
echo "Running platformMappginGen - requires a prior successful build using fbossctl"

FBOSS_DIR="/var/FBOSS"
SCRATCH_DIR="$FBOSS_DIR/tmp_build_dir"
fboss_output_dir=$(find $SCRATCH_DIR -maxdepth 1 -name "fboss_bins*")

PLATFORMMAPPING_GEN="$fboss_output_dir/bin/fboss-platform-mapping-gen"

if [ ! -e "$PLATFORMMAPPING_GEN" ]; then
    echo "$PLATFORMMAPPING_GEN doesn't exist. A prior successful build is required."
    exit 1
fi

# Check if an argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <platform-name>"
  echo "e.g. $0 meru800bia"
  exit 1
fi

platform=$(echo "$1" | tr '[:upper:]' '[:lower:]')
CONFIG_PATH="/var/FBOSS/fboss.git/arista/platform/$platform/config"

if [ -d "$CONFIG_PATH" ]; then
  echo "Found config directory: $CONFIG_PATH"
else
  echo "Please add vendor mapping CSVs under $CONFIG_PATH"
fi

# Copy fboss-platform-mapping-gen executable to the working directory of the Meta script
mkdir -p /tmp/fbcode_builder_getdeps-ZvarZFBOSSZfboss.gitZbuildZfbcode_builder-root/build/fboss
cp "$PLATFORMMAPPING_GEN" /tmp/fbcode_builder_getdeps-ZvarZFBOSSZfboss.gitZbuildZfbcode_builder-root/build/fboss

# Meta's helper script needs to be run from the root of the FBOSS repository.
cd /var/FBOSS/fboss.git
mkdir -p tmp/generated_platform_mappings/$platform
./fboss/lib/platform_mapping_v2/run-helper.sh \
--input-dir arista/platform/$platform/config/ \
--output-dir tmp/generated_platform_mappings/$platform \
--platform-name $platform

echo "Mapping files generated successfully"
echo "See configs located under tmp/generated_platform_mappings/$platform"
