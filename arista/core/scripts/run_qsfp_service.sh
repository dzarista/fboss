#!/bin/bash

BIN=/opt/fboss/bin/qsfp_service
CONF=/opt/fboss/share/wedge_agent/platform_wedge_agent.conf
QSFP_CONF=/opt/fboss/share/qsfp_service/platform_qsfp.conf
ARGS=(--thrift_ssl_policy=permitted)

# These config files are expected to be installed by the platform.
if [ -f "${QSFP_CONF}" ]; then
   ARGS+=(--qsfp-config "${QSFP_CONF}")
fi
if [ -f "${CONF}" ]; then
   ARGS+=(--config "${CONF}")
fi

nohup "${BIN}" "${ARGS[@]}"
