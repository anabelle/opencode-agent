#!/usr/bin/env bash
# Basic healthcheck for opencode
set -euo pipefail
TIMESTAMP=$(date --iso-8601=seconds)
LOAD=$(awk '{print $1}' /proc/loadavg)
DISK_USAGE=$(df --output=pcent / | tail -1 | tr -dc '0-9')
NETWORK_OK=1
# simple outbound check
if ! curl -sSf --max-time 5 https://example.com >/dev/null; then
  NETWORK_OK=0
fi
cat >> /home/ubuntu/opencode_actions.log <<EOF
${TIMESTAMP}	HEALTHCHECK	load=${LOAD}	disk=${DISK_USAGE}%	network_ok=${NETWORK_OK}
EOF
if (( DISK_USAGE > 80 )); then
  echo "DISK_THRESHOLD_EXCEEDED: ${DISK_USAGE}%" >&2
  exit 2
fi
if (( $(echo "$LOAD > 2.0" | bc -l) )); then
  echo "LOAD_THRESHOLD_EXCEEDED: ${LOAD}" >&2
  exit 3
fi
