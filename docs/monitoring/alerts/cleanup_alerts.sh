#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   bash docs/monitoring/alerts/cleanup_alerts.sh http://localhost:9201 "Nubla - Critical events spike" "Nubla - Ingest silence"
#
# Requisitos: jq

OS_URL="${1:-http://localhost:9201}"
shift || true

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq requerido" >&2
  exit 1
fi

if [ "$#" -eq 0 ]; then
  NAMES=("Nubla - Critical events spike" "Nubla - Ingest silence")
else
  NAMES=("$@")
fi

deleted=0
not_found=0

for name in "${NAMES[@]}"; do
  id=$(curl -sS -X POST "$OS_URL/_plugins/_alerting/monitors/_search" \
    -H 'Content-Type: application/json' \
    -d "$(jq -n --arg nm "$name" '{size:50, query:{term:{"monitor.name.keyword":$nm}}}')" \
    | jq -r '.hits.hits[0]._id // empty')

  if [ -n "$id" ]; then
    echo "Eliminando monitor: $name (id=$id)"
    curl -sS -X DELETE "$OS_URL/_plugins/_alerting/monitors/$id" | jq
    deleted=$((deleted+1))
  else
    echo "No encontrado (saltando): $name"
    not_found=$((not_found+1))
  fi
done

echo "Resumen: eliminados=$deleted, no_encontrados=$not_found"

echo "Verificación (no debería devolver coincidencias):"
curl -sS -X POST "$OS_URL/_plugins/_alerting/monitors/_search" \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --argjson arr "$(printf '%s\n' "${NAMES[@]}" | jq -R . | jq -s .)" '{size:50, query:{terms:{"monitor.name.keyword":$arr}}}')" | jq