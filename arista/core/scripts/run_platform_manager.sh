#!/bin/bash

BIN=/opt/fboss/bin/platform_manager
CONF=/opt/fboss/share/platform_configs/platform_manager.json
# FIXME: BUG912963 reduce the interval size once PM has been optimized for running as a deamon.
# It currently floods the console with logs everytime it reruns after the first time.
ARGS=(-config-file "${CONF}" -noenable_pkg_mgmnt -explore_interval_s 600)

"${BIN}" "${ARGS[@]}"