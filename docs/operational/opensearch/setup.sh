#!/usr/bin/env bash
set -euo pipefail

OS_URL="${1:-http://localhost:9201}"

echo "[1/6] Install/update ingest pipeline"
curl -sS -X PUT "$OS_URL/_ingest/pipeline/ensure_at_timestamp" \
  -H 'Content-Type: application/json' \
  -d @pipeline_ensure_at_timestamp.json | jq

echo "[2/6] Install/update index template"
curl -sS -X PUT "$OS_URL/_index_template/logs_template" \
  -H 'Content-Type: application/json' \
  -d @index_template_logs.json | jq

echo "[3/6] Create base index logs-default-000001 if missing (alias logs-default)"
if ! curl -sS "$OS_URL/logs-default-000001" | grep -q '"index"'; then
  curl -sS -X PUT "$OS_URL/logs-default-000001" \
    -H 'Content-Type: application/json' \
    -d '{"aliases":{"logs-default":{"is_write_index":true}}}' | jq
else
  echo "Index logs-default-000001 already exists"
fi

echo "[4/6] Install/update ISM policy"
curl -sS -X PUT "$OS_URL/_plugins/_ism/policies/logs-default-ism" \
  -H 'Content-Type: application/json' \
  -d @ism_policy_logs-default.json | jq

echo "[5/6] Attach policy to current write index"
curl -sS -X POST "$OS_URL/_plugins/_ism/add/logs-default-000001" \
  -H 'Content-Type: application/json' \
  -d '{"policy_id":"logs-default-ism"}' | jq || true

echo "[6/6] Optional manual rollover test (dry-run false)"
curl -sS -X POST "$OS_URL/logs-default/_rollover" \
  -H 'Content-Type: application/json' \
  -d '{"conditions":{"max_docs":1},"dry_run":true}' | jq

echo "Done."