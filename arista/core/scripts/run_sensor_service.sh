#!/bin/bash

BIN=/opt/fboss/bin/sensor_service
CONF=/opt/fboss/share/sensor_service/platform_sensors.conf
ARGS=()

# Config is provided by the platform.
if [ -f "${CONF}" ]; then
   ARGS+=(-config_path "${CONF}")
fi

"${BIN}" "${ARGS[@]}"
