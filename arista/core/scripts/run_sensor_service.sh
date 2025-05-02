#!/bin/bash

BIN=/opt/fboss/bin/sensor_service
CONF=/opt/fboss/share/platform_configs/sensor_service.json
ARGS=()

# Config is provided by the platform.
if [ -f "${CONF}" ]; then
   ARGS+=(-config_file "${CONF}")
fi

"${BIN}" "${ARGS[@]}"
