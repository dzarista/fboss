#!/bin/bash
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

# General-purpose wrapper to profile any command with flamegraphs.
#
# Usage: flamegraph.sh [OPTIONS] <command> [args...]
#        flamegraph.sh [OPTIONS] --pid PID
#
# Options:
#   -f, --freq FREQ         Perf sampling frequency (default: 99 Hz)
#   -o, --output DIR        Output directory (default: /tmp/flamegraph)
#   -n, --name NAME         Base name for output files (default: derived from command)
#   -p, --pid PID           Profile existing process by PID
#   -d, --duration SECONDS  Duration to profile in seconds (default: 60, only with --pid)
#   -h, --help              Show this help message
#
# Examples:
#   # Profile a command execution
#   flamegraph.sh fboss2 show port
#   flamegraph.sh thriftctl show port
#   flamegraph.sh --freq 999 fboss2 show port
#   flamegraph.sh -o /var/log/flamegraph -n mytest ./my_program
#
#   # Profile existing process by PID
#   flamegraph.sh --pid 1234 --duration 30
#   flamegraph.sh --pid 1234 --name qsfp_service --duration 60
#   flamegraph.sh --pid $(pgrep qsfp_service) --duration 30

set -e

FLAMEGRAPH_DIR="/opt/FlameGraph"
OUTPUT_DIR="/tmp/flamegraph"
PERF_FREQ=99
BASE_NAME=""
TARGET_PID=""
DURATION=60

show_help() {
    sed -n '5,28p' "$0" | sed 's/^# \?//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--freq)
            PERF_FREQ="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -n|--name)
            BASE_NAME="$2"
            shift 2
            ;;
        -p|--pid)
            TARGET_PID="$2"
            shift 2
            ;;
        -d|--duration)
            DURATION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            break
            ;;
    esac
done

# Validate arguments
if [ -z "$TARGET_PID" ] && [ $# -eq 0 ]; then
    echo "Error: No command or PID specified"
    show_help
fi

if [ -n "$TARGET_PID" ] && [ $# -gt 0 ]; then
    echo "Error: Cannot specify both --pid and a command"
    exit 1
fi

# output directory
mkdir -p "$OUTPUT_DIR"

# Generate a single flamegraph
generate_flamegraph() {
    local perf_data="$1"
    local svg_file="$2"
    local target="$3"
    local duration="$4"
    shift 4

    echo "Running perf record..."
    if [ -n "$target" ]; then
        # PID
        timeout $duration perf record -F $PERF_FREQ -g -p "$target" -o "$perf_data" 2>/dev/null || true
    else
        # Command
        perf record -F $PERF_FREQ -g -o "$perf_data" -- "$@"
    fi

    if [ ! -f "$perf_data" ] || [ ! -s "$perf_data" ]; then
        echo "Error: Perf data file not found or empty"
        return 1
    fi

    echo "Generating flamegraph..."
    perf script -i "$perf_data" 2>/dev/null | \
        perl "$FLAMEGRAPH_DIR/stackcollapse-perf.pl" | \
        perl "$FLAMEGRAPH_DIR/flamegraph.pl" > "$svg_file" 2>/dev/null

    if [ -s "$svg_file" ]; then
        SIZE=$(stat -c%s "$svg_file" 2>/dev/null || stat -f%z "$svg_file" 2>/dev/null)
        echo "Flamegraph: $svg_file (${SIZE} bytes)"
        return 0
    else
        echo "Error: Flamegraph generation failed (empty SVG)"
        return 1
    fi
}

# Check if process exists (for --pid mode)
if [ -n "$TARGET_PID" ]; then
    if ! kill -0 "$TARGET_PID" 2>/dev/null; then
        echo "Error: Process $TARGET_PID does not exist"
        exit 1
    fi
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -z "$BASE_NAME" ]; then
    if [ -n "$TARGET_PID" ]; then
        PROC_NAME=$(ps -p "$TARGET_PID" -o comm= 2>/dev/null | tr -cd '[:alnum:]_-')
        BASE_NAME="${PROC_NAME}_pid${TARGET_PID}_${TIMESTAMP}"
    else
        CMD_NAME=$(echo "$@" | tr ' ' '_' | tr -cd '[:alnum:]_-' | cut -c1-50)
        BASE_NAME="${CMD_NAME}_${TIMESTAMP}"
    fi
else
    BASE_NAME="${BASE_NAME}_${TIMESTAMP}"
fi

PERF_DATA="$OUTPUT_DIR/${BASE_NAME}.perf.data"
SVG_FILE="$OUTPUT_DIR/${BASE_NAME}.svg"

echo "=== FlameGraph Profiling ==="
if [ -n "$TARGET_PID" ]; then
    PROC_NAME=$(ps -p "$TARGET_PID" -o comm= 2>/dev/null)
    echo "Process: $PROC_NAME (PID: $TARGET_PID)"
    echo "Duration: ${DURATION}s"
else
    echo "Command: $@"
fi
echo "Frequency: ${PERF_FREQ} Hz"
echo ""

if generate_flamegraph "$PERF_DATA" "$SVG_FILE" "$TARGET_PID" "$DURATION" "$@"; then
    echo ""
    echo "=== Success ==="
    echo "Flamegraph: $SVG_FILE"
    echo "Perf data: $PERF_DATA"
else
    exit 1
fi

