#!/bin/bash

BIN=/opt/fboss/bin/qsfp_service
ARGS=(--thrift_ssl_policy=permitted)
ARGS+=(-multi_npu_platform_mapping)
"${BIN}" "${ARGS[@]}"
