#!/bin/bash

ARGS=()

# Find management interface.
MGMT_INTF=$(ip route get 8.8.8.8 | sed -n 's/.*dev \([^\ ]*\).*/\1/p')
if [ "${MGMT_INTF}" != "eth0" ]; then
   ARGS+=(--mgmt-if="${MGMT_INTF}")
fi

if BIN=$(find /opt/fboss/bin/* -type f -name wedge_agent*); then
   cd /opt/fboss && source bin/setup_fboss_env
   cd /opt/fboss && ./bin/setup.py --reload
   export DPP_DB_PATH=/opt/fboss/share/db
   "${BIN}" "${ARGS[@]}"
else
   echo "Failed to find wedge_agent binary in /opt/fboss/bin/"
   exit 1
fi
