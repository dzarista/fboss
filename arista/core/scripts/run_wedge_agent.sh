#!/bin/bash

FRU=/var/facebook/fboss/fruid.json
CONF=/opt/fboss/share/wedge_agent/platform_wedge_agent.conf
ARGS=()

# This config should be provided by the platform.
if [ -f "${CONF}" ]; then
   ARGS+=(--config "${CONF}")
fi

if [ -f "${FRU}" ]; then
   if MODEL_NAME=$(cat "${FRU}" | python3 -c "import sys, json; print(json.load(sys.stdin)['Information']['Product Name'])"); then
      ARGS+=(--mode "${MODEL_NAME,,}")
   fi
fi

if BIN=$(find /opt/fboss/bin/* -type f -name wedge_agent*); then
   nohup "${BIN}" "${ARGS[@]}"
else
   echo "Failed to find wedge_agent binary in /opt/fboss/bin/"
   exit 1
fi
