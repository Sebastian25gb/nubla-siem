#!/usr/bin/env bash
# Prepara alias de escritura "logs-<tenant>" -> "logs_<tenant>_000001" y migra datos si existe índice directo.
# Uso:
#   OPENSEARCH_URL=http://localhost:9201 TENANT_ID=default bash docs/operational/opensearch/bootstrap_alias_logs_default.sh
# Opcional: OPENSEARCH_USERNAME/OPENSEARCH_PASSWORD si tienes auth básica.

set -euo pipefail

OS_URL="${OPENSEARCH_URL:-http://localhost:9201}"
OS_USER="${OPENSEARCH_USERNAME:-}"
OS_PASS="${OPENSEARCH_PASSWORD:-}"
TENANT="${TENANT_ID:-default}"

BASE_UNDERSCORE="logs_${TENANT}"
FIRST_INDEX="${BASE_UNDERSCORE}_000001"   # logs_default_000001
WRITE_ALIAS="logs-${TENANT}"               # logs-default
DIRECT_INDEX="${WRITE_ALIAS}"              # índice directo que puede haber creado el consumer

auth_opts=()
if [[ -n "$OS_USER" || -n "$OS_PASS" ]]; then
  auth_opts=(-u "${OS_USER}:${OS_PASS}")
fi

jq_bin=$(command -v jq || true)
_curl() { command curl -sS "${auth_opts[@]}" "$@"; }

echo "OpenSearch URL: $OS_URL"
echo "Tenant: $TENANT"
echo "First index: $FIRST_INDEX"
echo "Write alias: $WRITE_ALIAS"

# 1) Crear índice versionado si no existe
HEAD_CODE=$(command curl -s -o /dev/null -w '%{http_code}' "${auth_opts[@]}" -X HEAD "${OS_URL}/${FIRST_INDEX}")
if [[ "$HEAD_CODE" != "200" ]]; then
  echo "Creating index ${FIRST_INDEX}..."
  _curl -X PUT "${OS_URL}/${FIRST_INDEX}" -H 'Content-Type: application/json' --data '{
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0
    }
  }' | ${jq_bin:-cat}
else
  echo "Index ${FIRST_INDEX} already exists."
fi

# 2) Apuntar alias de escritura al índice versionado (remueve alias previo y añade el nuevo)
echo "Ensuring alias ${WRITE_ALIAS} -> ${FIRST_INDEX} (is_write_index=true)..."
_curl -X POST "${OS_URL}/_aliases" -H 'Content-Type: application/json' --data "{
  \"actions\": [
    { \"remove\": { \"index\": \"*\", \"alias\": \"${WRITE_ALIAS}\" } },
    { \"add\": { \"index\": \"${FIRST_INDEX}\", \"alias\": \"${WRITE_ALIAS}\", \"is_write_index\": true } }
  ]
}" | ${jq_bin:-cat}

# 3) Si existe índice directo (logs-tenant), reindexar y borrarlo
DIRECT_EXISTS=$(command curl -s -o /dev/null -w '%{http_code}' "${auth_opts[@]}" -X HEAD "${OS_URL}/${DIRECT_INDEX}")
if [[ "$DIRECT_EXISTS" == "200" ]]; then
  echo "Direct index ${DIRECT_INDEX} exists. Reindexing into ${FIRST_INDEX} (conflicts=proceed)..."
  _curl -X POST "${OS_URL}/_reindex?wait_for_completion=true" -H 'Content-Type: application/json' --data "{
    \"source\": { \"index\": \"${DIRECT_INDEX}\" },
    \"dest\":   { \"index\": \"${FIRST_INDEX}\" },
    \"conflicts\": \"proceed\"
  }" | ${jq_bin:-cat}

  echo "Deleting direct index ${DIRECT_INDEX}..."
  _curl -X DELETE "${OS_URL}/${DIRECT_INDEX}" | ${jq_bin:-cat}
else
  echo "Direct index ${DIRECT_INDEX} not found. Nothing to migrate."
fi

# 4) Verificación rápida
echo "Alias resolution:"
_curl "${OS_URL}/_alias/${WRITE_ALIAS}" | ${jq_bin:-cat} || true

echo "Doc counts:"
echo "- ${FIRST_INDEX}:"
_curl "${OS_URL}/${FIRST_INDEX}/_count" | ${jq_bin:-cat}