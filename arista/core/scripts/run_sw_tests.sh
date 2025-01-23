echo "Running sw_tests - requires a prior successful build if using fbossctl"
dnf install -y double-conversion-devel xxhash-devel

TEST_PATH_REGEX=".*tests?$" 
HW_TEST_PATH_REGEX=".*hw_tests?$"

passed=()
failed=()

# Default to fboss build environment if no arg provided
BUILD_DIR="${1:-/var/FBOSS/tmp_build_dir/build/fboss}"

if [ -d "$BUILD_DIR" ]; then
    cd "$BUILD_DIR"
else
    echo "$BUILD_DIR doesn't exist. A prior successful build is required if using fbossctl."
    echo "If not using fbossctl, make sure you are correctly passing in the directory where the binaries are located"
    exit 1
fi

for file in *; do
    if [[ -x "$file" && "$file" =~ $TEST_PATH_REGEX && ! "$file" =~ $HW_TEST_PATH_REGEX ]]; then
        if [[ "$file" == "fan_service_sw_test" && "$BUILD_DIR" = "/var/FBOSS/tmp_build_dir/build/fboss" ]]; then
            # Must be run in a certain directory relative to the fan_service.json file
            cd "/var/FBOSS/fboss.git" && "./fan_service_sw_test"
            cd "$BUILD_DIR"
        else
            ./"$file"
        fi
        
        if [[ $? -eq 0 ]]; then
            passed+=("$file")
        else
            failed+=("$file")
        fi
    fi
done


echo
echo "Summary:"
echo "---------"
if [[ ${#passed[@]} -gt 0 ]]; then
    echo "Passed:"
    for p in "${passed[@]}"; do
        echo "  $p"
    done
else
    echo "No scripts passed."
fi

if [[ ${#failed[@]} -gt 0 ]]; then
    echo "Failed:"
    for f in "${failed[@]}"; do
        echo "  $f"
    done
else
    echo "No scripts failed."
fi
