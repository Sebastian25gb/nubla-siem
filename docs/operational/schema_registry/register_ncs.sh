#!/usr/bin/env bash
# Registra el schema NCS v1 en un Schema Registry compatible con Confluent API.
# Uso:
#   SCHEMA_REGISTRY_URL=http://localhost:8081 ./docs/operational/schema_registry/register_ncs.sh
# Requisitos: curl y jq disponibles en el host.

set -euo pipefail

SCHEMA_REGISTRY_URL="${SCHEMA_REGISTRY_URL:-http://localhost:8081}"
SCHEMA_FILE="docs/schema/ncs_schema_registry.json"
SUBJECT="${SUBJECT:-ncs-value}"    # subject convention: <subject>-value for message value schemas
SCHEMA_TYPE="${SCHEMA_TYPE:-JSON}" # JSON schema type

if [ ! -f "$SCHEMA_FILE" ]; then
  echo "ERROR: schema file not found: $SCHEMA_FILE"
  exit 1
fi

# Escape JSON schema into a single JSON string for POST body
SCHEMA_JSON_ESCAPED=$(jq -Rs '.' "$SCHEMA_FILE")

BODY=$(jq -n --arg schema "$SCHEMA_JSON_ESCAPED" --arg type "$SCHEMA_TYPE" '{schema: ($schema | tostring), schemaType: $type}')

echo "Registering subject '$SUBJECT' at ${SCHEMA_REGISTRY_URL}..."
echo "Request body (truncated):"
echo "$BODY" | jq '{schemaType, schema_length: (.schema|length)}'

HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/_sr_resp.json -X POST \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data "$BODY" \
  "${SCHEMA_REGISTRY_URL}/subjects/${SUBJECT}/versions")

RESP_BODY=$(cat /tmp/_sr_resp.json)

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
  echo "Schema registered successfully (http $HTTP_CODE):"
  echo "$RESP_BODY" | jq .
  exit 0
else
  echo "Failed to register schema (http $HTTP_CODE):"
  echo "$RESP_BODY" | jq . || echo "$RESP_BODY"
  exit 2
fi