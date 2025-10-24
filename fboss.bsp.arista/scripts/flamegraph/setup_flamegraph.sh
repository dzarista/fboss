#!/bin/bash
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

# Script to set up FlameGraph dependencies

set -e

echo "Installing FlameGraph dependencies..."

FLAMEGRAPH_DIR="/opt/FlameGraph"
FLAMEGRAPH_REPO="https://github.com/brendangregg/FlameGraph.git"

# Install dependencies
dnf install -y perf perl perl-open

# Install FlameGraph scripts
[ -d "$FLAMEGRAPH_DIR" ] && rm -rf "$FLAMEGRAPH_DIR"
git clone "$FLAMEGRAPH_REPO" "$FLAMEGRAPH_DIR"
chmod +x "$FLAMEGRAPH_DIR"/*.pl

echo "Setup complete! FlameGraph dependencies installed."
