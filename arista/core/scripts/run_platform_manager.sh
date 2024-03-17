#!/bin/bash

READY_FLAG="/tmp/platform_manager_ready.flag"
PM_SUCCESS_LOG="Completed setting up"

BIN=/opt/fboss/bin/platform_manager
CONF=/opt/fboss/share/platform_configs/platform_manager.json
# FIXME: BUG912963 reduce the interval size once PM has been optimized for running as a deamon.
# It currently floods the console with logs everytime it reruns after the first time.
ARGS=(-config-file "${CONF}" -noenable_pkg_mgmnt -explore_interval_s 3600 -reload_kmods=true)

PROCESS="$BIN ${ARGS[@]}"

rm -f "$READY_FLAG"

$PROCESS 2>&1 | while IFS= read -r line; do
    echo "$line"
    if [[ "$line" == *"$PM_SUCCESS_LOG"* ]]; then
        touch "$READY_FLAG"
    fi
done &

# Wait for ready flag
while [[ ! -f "$READY_FLAG" ]]; do sleep 1; done

# Set service status to active
systemd-notify --ready

# Keep the script running
sleep infinity
