#!/bin/bash

ARGS=()

# Find management interface.
MGMT_INTF=$(ip route get 8.8.8.8 | sed -n 's/.*dev \([^\ ]*\).*/\1/p')
if [ -n "${MGMT_INTF}" -a "${MGMT_INTF}" != "eth0" ]; then
   ARGS+=(--mgmt-if="${MGMT_INTF}")
fi

# Allow for running switch mutations. This is useful for the state sync script
# which grabs the state from remote leaf devices and executes patch APIs on
# the local leaf device.
ARGS+=(--allow_running_switch_state_mutations=true)

# Run in multi switch mode with multi npu platform mapping.
ARGS+=(-multi_npu_platform_mapping)
ARGS+=(-multi_switch)

if BIN=$(find /opt/fboss/bin/* -type f -name fboss_sw_agent*); then
   cd /opt/fboss && source bin/setup_fboss_env
   cd /opt/fboss && ./bin/setup.py --reload
   export DPP_DB_PATH=/opt/fboss/share/db
   "${BIN}" "${ARGS[@]}"
else
   echo "Failed to find fboss_sw_agent binary in /opt/fboss/bin/"
   exit 1
fi
