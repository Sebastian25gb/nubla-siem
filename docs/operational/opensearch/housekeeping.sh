#!/usr/bin/env bash
set -euo pipefail
OS_URL="${1:-http://localhost:9201}"

echo "[1/3] List indices"
curl -sS "$OS_URL/_cat/indices/logs-default-*?v"

echo "[2/3] Delete empty indices"
to_delete=$(curl -sS "$OS_URL/_cat/indices/logs-default-*?h=index,docs.count" | awk '$2=="0"{print $1}')
for idx in $to_delete; do
  echo "Deleting $idx"
  curl -sS -X DELETE "$OS_URL/$idx" | jq
done

echo "[3/3] Alias status"
curl -sS "$OS_URL/_alias/logs-default" | jq