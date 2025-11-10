#!/usr/bin/env bash
# Bootstrap minimal para OpenSearch (dev). Ejecutar desde la máquina host
# Requisitos: curl y jq en el host; OpenSearch accesible en http://localhost:9201

set -euo pipefail

OPENSEARCH_HOST="${OPENSEARCH_HOST:-http://localhost:9201}"
TEMPLATE_PATH="docs/operational/opensearch/logs_tenant_template.json"
TEMPLATE_NAME="template_logs"

echo "Subiendo template ${TEMPLATE_NAME} a ${OPENSEARCH_HOST}"
curl -sS -X PUT "${OPENSEARCH_HOST}/_index_template/${TEMPLATE_NAME}" \
  -H "Content-Type: application/json" \
  --data-binary @"${TEMPLATE_PATH}" | jq .

echo "Comprobando template listado..."
curl -sS "${OPENSEARCH_HOST}/_index_template/${TEMPLATE_NAME}" | jq .

echo "Creando índice de prueba logs_default_000001 (replicas=0)..."
curl -sS -X PUT "${OPENSEARCH_HOST}/logs_default_000001" -H "Content-Type: application/json" -d '{
  "settings": { "index": { "number_of_shards": 1, "number_of_replicas": 0 } }
}' | jq .

echo "Indexando documento de prueba..."
curl -sS -X POST "${OPENSEARCH_HOST}/logs_default_000001/_doc?refresh=wait_for" \
  -H "Content-Type: application/json" \
  -d '{
    "@timestamp":"2025-11-10T16:20:00Z",
    "tenant_id":"default",
    "dataset":"syslog.generic",
    "message":"evento de prueba desde bootstrap",
    "severity":"info",
    "source": {"ip":"127.0.0.1"}
  }' | jq .

echo "Buscando documento de prueba..."
curl -sS "${OPENSEARCH_HOST}/logs_default_*/_search?q=tenant_id:default&pretty" | jq .

echo "Bootstrap completado."