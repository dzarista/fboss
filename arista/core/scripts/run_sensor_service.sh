#!/bin/bash

BIN=/opt/fboss/bin/sensor_service
CONF=/opt/fboss/share/platform_configs/sensor_service.json
ARGS=()

# If platform_manager is running, wait until it has finished setup.
READY_FLAG="/tmp/platform_manager_ready.flag"
if [ -f /opt/fboss/share/platform_configs/platform_manager.json ]; then
   echo "Waiting for Platform manager to complete setup..."
   while [ ! -f "$READY_FLAG" ]; do
      sleep 1
   done
   echo "Completed setup by platform manager Detected. Resuming sensor_service."
fi

# Config is provided by the platform.
if [ -f "${CONF}" ]; then
   ARGS+=(-config_file "${CONF}")
fi

"${BIN}" "${ARGS[@]}"
