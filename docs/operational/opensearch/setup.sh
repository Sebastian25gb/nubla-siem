#!/usr/bin/env bash
set -euo pipefail

OS_URL="${1:-http://localhost:9201}"

jq_bin=$(command -v jq || true)
if [ -z "$jq_bin" ]; then
  echo "jq is required in PATH" >&2
  exit 1
fi

echo "[1/9] Install/update ingest pipeline: ensure_at_timestamp"
curl -sS -X PUT "$OS_URL/_ingest/pipeline/ensure_at_timestamp" \
  -H 'Content-Type: application/json' \
  -d @pipeline_ensure_at_timestamp.json | jq

echo "[2/9] Install/update ingest pipeline: logs_ingest"
curl -sS -X PUT "$OS_URL/_ingest/pipeline/logs_ingest" \
  -H 'Content-Type: application/json' \
  -d @pipeline_logs_ingest.json | jq

echo "[3/9] Install/update index template"
curl -sS -X PUT "$OS_URL/_index_template/logs_template" \
  -H 'Content-Type: application/json' \
  -d @index_template_logs.json | jq

echo "[4/9] Create base index logs-default-000001 if missing"
if ! curl -sS "$OS_URL/logs-default-000001" | grep -q '"index"'; then
  curl -sS -X PUT "$OS_URL/logs-default-000001" \
    -H 'Content-Type: application/json' \
    -d '{"aliases":{"logs-default":{"is_write_index":true}}}' | jq
else
  echo "Index logs-default-000001 already exists"
fi

echo "[5/9] Detect write index"
write_index=$(curl -sS "$OS_URL/_alias/logs-default" | jq -r 'to_entries[] | select(.value.aliases["logs-default"].is_write_index == true) | .key')
if [ -z "$write_index" ] || [ "$write_index" = "null" ]; then
  write_index="logs-default-000001"
fi
echo "Write index: $write_index"

echo "[6/9] Ensure rollover_alias + default_pipeline on write index"
curl -sS -X PUT "$OS_URL/$write_index/_settings" \
  -H 'Content-Type: application/json' \
  -d '{"index":{"opendistro.index_state_management.rollover_alias":"logs-default","default_pipeline":"logs_ingest"}}' | jq

echo "[7/9] Install/update ISM policy"
curl -sS -X PUT "$OS_URL/_plugins/_ism/policies/logs-default-ism" \
  -H 'Content-Type: application/json' \
  -d @ism_policy_logs-default.json | jq || true

echo "[8/9] Attach policy to write index"
curl -sS -X POST "$OS_URL/_plugins/_ism/add/$write_index" \
  -H 'Content-Type: application/json' \
  -d '{"policy_id":"logs-default-ism"}' | jq || true

echo "[9/9] Reprocess write index via logs_ingest"
curl -sS -X POST "$OS_URL/$write_index/_update_by_query?conflicts=proceed&pipeline=logs_ingest" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match_all":{}}}' | jq

echo "Done."