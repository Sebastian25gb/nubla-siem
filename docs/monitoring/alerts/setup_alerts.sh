#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   bash docs/monitoring/alerts/setup_alerts.sh http://localhost:9201
# Variables opcionales (exportar antes o inline):
#   DEST_URL="http://localhost:9999/alert"
#   INDEX_ALIAS="logs-default"
#   CRIT_THRESHOLD=50
#   SILENCE_WINDOW="10m"
#
# Dependencias: jq

OS_URL="${1:-http://localhost:9201}"
INDEX_ALIAS="${INDEX_ALIAS:-logs-default}"
CRIT_THRESHOLD="${CRIT_THRESHOLD:-50}"
SILENCE_WINDOW="${SILENCE_WINDOW:-10m}"
DEST_URL="${DEST_URL:-}"

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq requerido" >&2
  exit 1
fi

echo "[1/5] Preparando canal de notificaciones (opcional)"
channel_id=""
if [ -n "$DEST_URL" ]; then
  # Intentar crear canal webhook
  create_resp=$(curl -sS -X POST "$OS_URL/_plugins/_notifications/configs" \
     -H 'Content-Type: application/json' \
     -d "$(jq -n \
        --arg url "$DEST_URL" \
        '{name:"Nubla Webhook",config_type:"webhook",is_enabled:true,webhook:{url:$url,header_params:{},method:"POST"}}')") || true

  channel_id=$(echo "$create_resp" | jq -r '.config_id // empty')

  if [ -z "$channel_id" ]; then
    # Buscar si ya existe
    list_resp=$(curl -sS "$OS_URL/_plugins/_notifications/configs?from_index=0&max_items=1000")
    channel_id=$(echo "$list_resp" | jq -r '.config_list[] | select(.name=="Nubla Webhook") | .config_id' | head -n1)
    if [ -n "$channel_id" ]; then
      echo "Canal reutilizado: $channel_id"
    else
      echo "WARN: No se pudo crear ni encontrar canal; monitores sin acciones."
    fi
  else
    echo "Canal creado: $channel_id"
  fi
else
  echo "DEST_URL no definido: monitores se crean sin acciones."
fi

echo "[2/5] Definiendo JSON monitor Critical events spike"
crit_monitor_json=$(jq -n \
  --arg name "Nubla - Critical events spike" \
  --arg idx "$INDEX_ALIAS" \
  --argjson threshold "$CRIT_THRESHOLD" \
  --arg channel "$channel_id" '
{
  type: "monitor",
  name: $name,
  enabled: true,
  schedule: { period: { interval: 1, unit: "MINUTES" } },
  inputs: [
    {
      search: {
        indices: [$idx],
        query: {
          size: 0,
          query: {
            bool: {
              filter: [
                { term: { severity: "critical" } },
                { range: { "@timestamp": { gte: "now-5m", lte: "now" } } }
              ]
            }
          }
        }
      }
    }
  ],
  triggers: [
    {
      query_level_trigger: {
        name: "critical_above_threshold",
        severity: "2",
        condition: {
          script: {
            lang: "painless",
            source: "return ctx.results[0].hits.total.value > params.threshold",
            params: { threshold: $threshold }
          }
        },
        actions: (if $channel != "" then [
          {
            name: "notify-critical-spike",
            destination_id: $channel,
            message_template: { source: ("Critical spike: {{ctx.monitor.name}} count={{ctx.results.0.hits.total.value}} threshold=" + ($threshold|tostring)) },
            throttle_enabled: false
          }
        ] else [] end)
      }
    }
  ]
}')

echo "[3/5] Creando/actualizando monitor crítico"
existing_crit_id=$(curl -sS -X POST "$OS_URL/_plugins/_alerting/monitors/_search" \
  -H 'Content-Type: application/json' \
  -d '{"size":100,"query":{"term":{"monitor.name.keyword":"Nubla - Critical events spike"}}}' | jq -r '.hits.hits[0]._id // empty')

if [ -n "$existing_crit_id" ]; then
  echo "Encontrado monitor crítico existente: $existing_crit_id → actualizando"
  curl -sS -X PUT "$OS_URL/_plugins/_alerting/monitors/$existing_crit_id" \
    -H 'Content-Type: application/json' \
    -d "$crit_monitor_json" | jq
else
  echo "Creando monitor crítico nuevo"
  curl -sS -X POST "$OS_URL/_plugins/_alerting/monitors" \
    -H 'Content-Type: application/json' \
    -d "$crit_monitor_json" | jq
fi

echo "[4/5] Definiendo JSON monitor Ingest silence"
silence_monitor_json=$(jq -n \
  --arg name "Nubla - Ingest silence" \
  --arg idx "$INDEX_ALIAS" \
  --arg window "$SILENCE_WINDOW" \
  --arg channel "$channel_id" '
{
  type: "monitor",
  name: $name,
  enabled: true,
  schedule: { period: { interval: 1, unit: "MINUTES" } },
  inputs: [
    {
      search: {
        indices: [$idx],
        query: {
          size: 0,
          query: { range: { "@timestamp": { gte: ("now-" + $window), lte: "now" } } }
        }
      }
    }
  ],
  triggers: [
    {
      query_level_trigger: {
        name: "no_ingest_window",
        severity: "3",
        condition: {
          script: {
            lang: "painless",
            source: "return ctx.results[0].hits.total.value == 0"
          }
        },
        actions: (if $channel != "" then [
          {
            name: "notify-silence",
            destination_id: $channel,
            message_template: { source: ("Silence detected: {{ctx.monitor.name}} window=" + $window) },
            throttle_enabled: false
          }
        ] else [] end)
      }
    }
  ]
}')

echo "[5/5] Creando/actualizando monitor de silencio"
existing_silence_id=$(curl -sS -X POST "$OS_URL/_plugins/_alerting/monitors/_search" \
  -H 'Content-Type: application/json' \
  -d '{"size":100,"query":{"term":{"monitor.name.keyword":"Nubla - Ingest silence"}}}' | jq -r '.hits.hits[0]._id // empty')

if [ -n "$existing_silence_id" ]; then
  echo "Encontrado monitor de silencio existente: $existing_silence_id → actualizando"
  curl -sS -X PUT "$OS_URL/_plugins/_alerting/monitors/$existing_silence_id" \
    -H 'Content-Type: application/json' \
    -d "$silence_monitor_json" | jq
else
  echo "Creando monitor de silencio nuevo"
  curl -sS -X POST "$OS_URL/_plugins/_alerting/monitors" \
    -H 'Content-Type: application/json' \
    -d "$silence_monitor_json" | jq
fi

echo "--- Monitores instalados (búsqueda por nombres) ---"
curl -sS -X POST "$OS_URL/_plugins/_alerting/monitors/_search" \
  -H 'Content-Type: application/json' \
  -d '{"size":50,"query":{"terms":{"monitor.name.keyword":["Nubla - Critical events spike","Nubla - Ingest silence"]}}}' | jq

echo "Done."