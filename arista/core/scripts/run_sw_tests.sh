echo "Running sw_tests - requires a prior successful build"
echo "This script needs to be run from arista-fboss root"

# Add failing test binaries we should ignore to this list
EXCLUDE_BIN_LIST=(
    # Skipping bsp_tests from running as it causes the script to report a failure
    # TODO: 1226925 [FBOSS] running & generating bsp_tests internally
    bsp_tests
    # bb/1277145: Skipping platform testing
    platform_manager_platform_explorer_test
    platform_mapping_gen_no_regression_test
)

# Add failing gtest cases  we should ignore to this list
EXCLUDE_GTEST_LIST=(
    # "UtilsTest.ParseDevicePath"
)

gtest_filter=-$(IFS=:; echo "${EXCLUDE_LIST[*]}")
bin_filter=$(for i in ${EXCLUDE_BIN_LIST[*]}; do echo "-not -name $i"; done)
test_regex=".*tests?$"
hwtest_regex=".*hw_tests?$"

passed=()
failed=()

# Default to fboss build environment if no arg provided
BUILD_DIR="${1:-/var/FBOSS/tmp_build_dir/build/fboss}"

if [ ! -d "$BUILD_DIR" ]; then
    echo "$BUILD_DIR doesn't exist. A prior successful build is required if using fbossctl."
    echo "If not using fbossctl, make sure you are correctly passing in the directory where the binaries are located"
    exit 1
fi

tests=$(find $BUILD_DIR -type f -executable -regex $test_regex -not -regex $hwtest_regex $bin_filter)
for test in $tests; do
    $test --gtest_filter=$gtest_filter
    if [[ $? -eq 0 ]]; then
        passed+=($(basename "$test"))
    else
        failed+=($(basename "$test"))
    fi
done

echo
echo "Summary:"
echo "---------"
if [[ ${#passed[@]} -gt 0 ]]; then
    echo "Passed:"
    echo "${passed[*]}"
else
    echo "No scripts passed."
fi

if [[ ${#EXCLUDE_LIST[@]} -gt 0 ]]; then
    echo "Skipped:"
    echo "${EXCLUDE_LIST[*]}"
fi

if [[ ${#failed[@]} -gt 0 ]]; then
    echo "Failed:"
    echo "${failed[*]}"
    exit 1
else
    echo "No scripts failed."
fi
