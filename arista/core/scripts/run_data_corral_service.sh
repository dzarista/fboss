#!/bin/bash

BIN=/opt/fboss/bin/data_corral_service
CONF=/opt/fboss/share/platform_configs/led_manager.json
ARGS=()

# Config is provided by the platform.
if [ -f "${CONF}" ]; then
   ARGS+=(-config_file "${CONF}")
fi

"${BIN}" "${ARGS[@]}"
