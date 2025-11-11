#!/usr/bin/env bash
set -euo pipefail

OS_URL="${1:-http://localhost:9201}"

jq_bin=$(command -v jq || true)
if [ -z "$jq_bin" ]; then
  echo "jq is required in PATH" >&2
  exit 1
fi

echo "[1/7] Install/update ingest pipeline"
curl -sS -X PUT "$OS_URL/_ingest/pipeline/ensure_at_timestamp" \
  -H 'Content-Type: application/json' \
  -d @pipeline_ensure_at_timestamp.json | jq

echo "[2/7] Install/update index template"
curl -sS -X PUT "$OS_URL/_index_template/logs_template" \
  -H 'Content-Type: application/json' \
  -d @index_template_logs.json | jq

echo "[3/7] Create base index logs-default-000001 if missing (alias logs-default)"
if ! curl -sS "$OS_URL/logs-default-000001" | grep -q '"index"'; then
  curl -sS -X PUT "$OS_URL/logs-default-000001" \
    -H 'Content-Type: application/json' \
    -d '{"aliases":{"logs-default":{"is_write_index":true}}}' | jq
else
  echo "Index logs-default-000001 already exists"
fi

echo "[4/7] Ensure rollover_alias setting on current write index"
# Detect current write index for alias logs-default
write_index=$(curl -sS "$OS_URL/_alias/logs-default" | jq -r '
  to_entries[]
  | select(.value.aliases["logs-default"].is_write_index == true)
  | .key
')
if [ -z "$write_index" ] || [ "$write_index" = "null" ]; then
  # fallback to base index
  write_index="logs-default-000001"
fi
echo "Write index detected: $write_index"

# Set rollover_alias setting on write index
curl -sS -X PUT "$OS_URL/$write_index/_settings" \
  -H 'Content-Type: application/json' \
  -d '{"index":{"opendistro.index_state_management.rollover_alias":"logs-default"}}' | jq

echo "[5/7] Install/update ISM policy"
curl -sS -X PUT "$OS_URL/_plugins/_ism/policies/logs-default-ism" \
  -H 'Content-Type: application/json' \
  -d @ism_policy_logs-default.json | jq

echo "[6/7] Attach policy to current write index ($write_index)"
curl -sS -X POST "$OS_URL/_plugins/_ism/add/$write_index" \
  -H 'Content-Type: application/json' \
  -d '{"policy_id":"logs-default-ism"}' | jq || true

echo "[7/7] Optional manual rollover test (dry-run)"
curl -sS -X POST "$OS_URL/logs-default/_rollover" \
  -H 'Content-Type: application/json' \
  -d '{"conditions":{"max_docs":1},"dry_run":true}' | jq

echo "Done."