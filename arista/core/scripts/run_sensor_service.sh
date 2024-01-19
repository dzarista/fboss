#!/bin/bash

BIN=/opt/fboss/bin/sensor_service
CONF=/opt/fboss/share/platform_configs/sensor_service.json
ARGS=()

# If platform_manager is setup, wait until it has finished setup.
PM_SUCCESS_LOG="SUCCESS. Completed setting up all the devices."
READY_FLAG="/tmp/platform_manager_ready.flag"
if [ -f /opt/fboss/share/platform_configs/platform_manager.json ]; then
   echo "Waiting for Platform manager to complete setup..."
    
   journalctl -fu platform_manager.service --since "5 seconds ago" | grep --line-buffered "$PM_SUCCESS_LOG" > "$READY_FLAG" 2>/dev/null &
   JOURNALCTL_PID=$!

   while : ; do
      if [ -s "$READY_FLAG" ]; then
         echo "Completed setup by platform manager Detected. Resuming sensor_service."
         break
      fi

      sleep 5 #Check once every 5 seconds
   done

   # Clean up
   kill $JOURNALCTL_PID
   rm -f "$READY_FLAG"
fi

# Config is provided by the platform.
if [ -f "${CONF}" ]; then
   ARGS+=(-config_file "${CONF}")
fi

"${BIN}" "${ARGS[@]}"
