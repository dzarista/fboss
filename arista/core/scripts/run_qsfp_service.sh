#!/bin/bash

BIN=/opt/fboss/bin/qsfp_service
ARGS=(--thrift_ssl_policy=permitted)
"${BIN}" "${ARGS[@]}"
