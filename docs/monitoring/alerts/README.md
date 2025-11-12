# Alertas OpenSearch (Monitores)

Se instalan dos monitores:

## 1. Nubla - Critical events spike
- Evalúa cada minuto.
- Cuenta documentos con `severity: critical` últimos 5 minutos.
- Dispara condición si `count > CRIT_THRESHOLD` (default: 50).
- Trigger severity = "2".

## 2. Nubla - Ingest silence
- Evalúa cada minuto.
- Busca documentos en ventana `SILENCE_WINDOW` (default: 10m).
- Dispara si `count == 0`.
- Trigger severity = "3".

## Notificaciones (Webhook opcional)
Define `DEST_URL` para crear canal tipo webhook (Notifications plugin):
```bash
DEST_URL="http://localhost:9999/alert"
```
Si no se define, monitores se crean sin acciones (puedes agregarlas luego desde Dashboards).

## Instalación
```bash
cd docs/monitoring/alerts
bash setup_alerts.sh http://localhost:9201
```

Con variables:
```bash
cd docs/monitoring/alerts
INDEX_ALIAS="logs-default" CRIT_THRESHOLD=30 SILENCE_WINDOW="5m" \
bash setup_alerts.sh http://localhost:9201
```

Con webhook:
```bash
cd docs/monitoring/alerts
DEST_URL="http://localhost:9999/alert" \
CRIT_THRESHOLD=40 SILENCE_WINDOW="8m" \
bash setup_alerts.sh http://localhost:9201
```

## Verificación
Listar monitores instalados:
```bash
curl -sS -X POST 'http://localhost:9201/_plugins/_alerting/monitors/_search' \
  -H 'Content-Type: application/json' \
  -d '{"size":50,"query":{"terms":{"monitor.name.keyword":["Nubla - Critical events spike","Nubla - Ingest silence"]}}}' | jq
```

## Forzar disparo crítico
Publica > CRIT_THRESHOLD eventos con `severity=critical` en menos de 5 minutos y luego revisa:
- Estado y último run en Dashboards (Alerting → Monitors).
- Trigger evaluado.

## Forzar silencio
Detén productores durante más de SILENCE_WINDOW y verifica condición.

## Errores comunes
| Error | Causa | Solución |
|-------|-------|----------|
| json_parse_exception | JSON mal formado (faltaba wrapper query_level_trigger) | Usar script corregido |
| unrecognized parameters [from],[size] | Parámetros enviados en query en vez de body | Enviar desde body JSON |
| 404 Notifications | Plugin Notifications no instalado | Instalar plugin o omitir DEST_URL |
| Monitor sin acciones | canal_id vacío | Revisar creación de webhook y permisos |

## Limpieza
Eliminar monitores:
```bash
for name in "Nubla - Critical events spike" "Nubla - Ingest silence"; do
  id=$(curl -sS -X POST 'http://localhost:9201/_plugins/_alerting/monitors/_search' \
    -H 'Content-Type: application/json' \
    -d "{\"size\":50,\"query\":{\"term\":{\"monitor.name.keyword\":\"$name\"}}}" | jq -r '.hits.hits[0]._id // empty')
  if [ -n "$id" ]; then
    curl -sS -X DELETE "http://localhost:9201/_plugins/_alerting/monitors/$id" | jq
  fi
done
```

## Próximos pasos
- Añadir monitor bucket_level para top host crítico.
- Añadir acción throttle (evitar spam).
- Integrar canal correo/Slack (otra config en Notifications).