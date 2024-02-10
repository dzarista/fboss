#!/bin/bash

# If platform_manager is running, wait until it has finished setup.
READY_FLAG="/tmp/platform_manager_ready.flag"
if [ -f /opt/fboss/share/platform_configs/platform_manager.json ]; then
   echo "Waiting for Platform manager to complete setup..."
   while [ ! -f "$READY_FLAG" ]; do
      sleep 1
   done
   echo "Completed setup by platform manager Detected. Resuming qsfp_service."
fi

BIN=/opt/fboss/bin/qsfp_service
ARGS=(--thrift_ssl_policy=permitted)
"${BIN}" "${ARGS[@]}"
