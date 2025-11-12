#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   bash docs/monitoring/alerts/disable_alerts.sh http://localhost:9201 "Nubla - Critical events spike" "Nubla - Ingest silence"
# Deshabilita (enabled=false) conservando los monitores.

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

disabled=0
not_found=0

for name in "${NAMES[@]}"; do
  hit=$(curl -sS -X POST "$OS_URL/_plugins/_alerting/monitors/_search" \
    -H 'Content-Type: application/json' \
    -d "$(jq -n --arg nm "$name" '{size:50, query:{term:{"monitor.name.keyword":$nm}}}')" )

  id=$(echo "$hit" | jq -r '.hits.hits[0]._id // empty')
  if [ -z "$id" ]; then
    echo "No encontrado (saltando): $name"
    not_found=$((not_found+1))
    continue
  fi

  src=$(echo "$hit" | jq -r '.hits.hits[0]._source')
  # Forzar enabled=false
  new_src=$(echo "$src" | jq '.enabled=false')

  echo "Deshabilitando monitor: $name (id=$id)"
  curl -sS -X PUT "$OS_URL/_plugins/_alerting/monitors/$id" \
    -H 'Content-Type: application/json' \
    -d "$new_src" | jq
  disabled=$((disabled+1))
done

echo "Resumen: deshabilitados=$disabled, no_encontrados=$not_found"

echo "Verificación (enabled=false):"
curl -sS -X POST "$OS_URL/_plugins/_alerting/monitors/_search" \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --argjson arr "$(printf '%s\n' "${NAMES[@]}" | jq -R . | jq -s .)" '{size:50, query:{terms:{"monitor.name.keyword":$arr}}}')" \
  | jq '.hits.hits[] | {id:._id, name:._source.name, enabled: ._source.enabled}'