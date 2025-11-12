#!/usr/bin/env bash
# scripts/check_dlq.sh
# Consulta la API Management de RabbitMQ y alerta si la DLQ supera THRESHOLD.
set -euo pipefail

RABBIT_HOST="${RABBIT_HOST:-localhost}"
RABBIT_PORT="${RABBIT_PORT:-15672}"
RABBIT_USER="${RABBIT_USER:-admin}"
RABBIT_PASS="${RABBIT_PASS:-securepass}"
QUEUE="${QUEUE:-logs_siem.dlq}"
THRESHOLD="${THRESHOLD:-10}"
LOGFILE="${LOGFILE:-/var/log/check_dlq.log}"
WEBHOOK="${WEBHOOK:-}"

API="http://${RABBIT_HOST}:${RABBIT_PORT}/api/queues/%2F/${QUEUE}"

resp=$(curl -sS -u "${RABBIT_USER}:${RABBIT_PASS}" "${API}" || true)
if [ -z "$resp" ]; then
  echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') - ERROR querying ${API}" | tee -a "$LOGFILE"
  exit 2
fi

count=$(printf '%s' "$resp" | jq -r '.messages // 0')
if [ "$count" -gt "$THRESHOLD" ]; then
  msg="$(date -u +'%Y-%m-%dT%H:%M:%SZ') - ALERT: DLQ ${QUEUE} depth ${count} > ${THRESHOLD}"
  echo "$msg" | tee -a "$LOGFILE"
  if [ -n "$WEBHOOK" ]; then
    curl -sS -X POST -H 'Content-Type: application/json' -d "{\"text\":\"${msg}\"}" "$WEBHOOK" || true
  fi
fi

exit 0