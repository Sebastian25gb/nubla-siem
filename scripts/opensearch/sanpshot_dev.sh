#!/bin/sh
# Simple snapshot script for dev. Expects dev_backup repo registered and path.repo mounted.
set -eu

ES_URL="${ES_URL:-http://localhost:9201}"
REPO="${REPO:-dev_backup}"
INDICES="${INDICES:-logs-default-*}"
SNAPNAME="${SNAPNAME:-logs-default-$(date -u +%Y%m%dT%H%M%SZ | tr '[:upper:]' '[:lower:]')}"

echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') Snapshot start: $SNAPNAME"

resp=$(curl -sS -XPUT "${ES_URL}/_snapshot/${REPO}/${SNAPNAME}?wait_for_completion=true" \
  -H 'Content-Type: application/json' \
  -d "{
    \"indices\": \"${INDICES}\",
    \"include_global_state\": false
  }" || true)

echo "$resp" | jq . || echo "$resp"

state=$(echo "$resp" | jq -r '.snapshot.state // empty' || true)
if [ "$state" = "SUCCESS" ]; then
  echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') Snapshot finished SUCCESS: ${SNAPNAME}"
  exit 0
else
  echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') Snapshot finished with state: ${state:-ERROR}"
  exit 2
fi