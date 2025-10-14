#!/bin/bash

BIN=/opt/fboss/bin/fan_service
CONF=/opt/fboss/share/platform_configs/fan_service.json
ARGS=()

# Config is provided by the platform.
if [ -f "${CONF}" ]; then
   ARGS+=(-config_file "${CONF}")
fi

"${BIN}" "${ARGS[@]}"
