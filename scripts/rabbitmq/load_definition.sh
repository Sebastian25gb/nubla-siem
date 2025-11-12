#!/usr/bin/env bash
set -euo pipefail

HOST="${RABBITMQ_HOST:-rabbitmq}"
PORT="${RABBITMQ_MGMT_PORT:-15672}"
USER="${RABBITMQ_USER:-admin}"
PASS="${RABBITMQ_PASSWORD:-securepass}"
DEFINITIONS_PATH="/defs/definitions.json"
MAX_RETRIES=60
SLEEP=2

echo "Waiting for RabbitMQ management API at http://$HOST:$PORT ..."
for i in $(seq 1 $MAX_RETRIES); do
  if curl -sS -u "$USER:$PASS" "http://$HOST:$PORT/api/healthchecks/node" >/dev/null 2>&1; then
    echo "RabbitMQ management API reachable."
    break
  fi
  echo "Waiting... ($i/$MAX_RETRIES)"
  sleep $SLEEP
done

if [ ! -f "$DEFINITIONS_PATH" ]; then
  echo "Definitions file not found: $DEFINITIONS_PATH"
  exit 1
fi

echo "Loading definitions from $DEFINITIONS_PATH (idempotent)..."
resp=$(curl -sS -u "$USER:$PASS" -H "Content-Type: application/json" -XPUT "http://$HOST:$PORT/api/definitions" -d @"$DEFINITIONS_PATH" || true)
echo "Response from RabbitMQ API:"
echo "$resp"
echo "Done."