#!/bin/bash

ARGS=()

if [ $# -lt 1 ]; then
   echo "Usage: run_hw_agent.sh <switchIndex>"
   exit 1
fi

ARGS+=(--switchIndex="$1")
shift

if BIN=$(find /opt/fboss/bin/* -type f -name fboss_hw_agent*); then
   cd /opt/fboss && source bin/setup_fboss_env
   export DPP_DB_PATH=/opt/fboss/share/db
   "${BIN}" "${ARGS[@]}"
else
   echo "Failed to find fboss_hw_agent binary in /opt/fboss/bin/"
   exit 1
fi
