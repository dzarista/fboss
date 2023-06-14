#!/bin/bash

ARGS=()

# Find management interface.
MGMT_INTF=$(ip route get 8.8.8.8 | sed -n 's/.*dev \([^\ ]*\).*/\1/p')
if [ -f "${CONF}" ]; then
   ARGS+=(--mgmt-if="${MGMT_INTF}")
fi

if BIN=$(find /opt/fboss/bin/* -type f -name wedge_agent*); then
   nohup "${BIN}" "${ARGS[@]}"
else
   echo "Failed to find wedge_agent binary in /opt/fboss/bin/"
   exit 1
fi
