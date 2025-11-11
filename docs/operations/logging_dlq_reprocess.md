# Reproceso de Dead Letter Queue (DLQ)

## Objetivo
Permite inspeccionar y corregir mensajes inválidos (validation_failed) y reinyectarlos al flujo normal.

## Script
`backend/app/tools/reprocess_dlq.py`

## Opciones CLI principales
| Flag | Descripción | Default |
|------|-------------|---------|
| --host | Host RabbitMQ | rabbitmq (o localhost) |
| --port | Puerto | 5672 |
| --user | Usuario | admin |
| --password | Password | securepass |
| --vhost | Virtual host | / |
| --dlq | Nombre de la cola DLQ | logs_siem.dlq |
| --exchange | Exchange destino | logs_default |
| --routing-key | Routing key destino | nubla.log.default |
| --limit | Máx mensajes a procesar | 100 |
| --dry-run | No publica, requeue los mensajes | False |
| --severity-default | Valor por defecto si falta severity | info |
| --sleep | Pausa (segundos) entre mensajes | 0.0 |
| --verbose | Salida detallada por mensaje | False |

## Ejemplos

Dry-run (no altera la cola permanentemente):
```bash
python backend/app/tools/reprocess_dlq.py --host localhost --dlq logs_siem.dlq --limit 20 --dry-run --verbose
```

Reproceso real:
```bash
python backend/app/tools/reprocess_dlq.py --host localhost --dlq logs_siem.dlq --limit 50 --severity-default info
```

Salida (ejemplo):
```json
{
  "summary": {
    "processed": 50,
    "published": 48,
    "requeued_dry_run": 0,
    "invalid_json": 2,
    "limit": 50,
    "dry_run": false
  }
}
```

## Estrategia Recomendada
1. Ejecutar primero en `--dry-run` para revisar transformaciones.
2. Ajustar severidad por defecto si es necesario.
3. Publicar en tandas pequeñas (ej. 100 mensajes) para evitar picos repentinos de ingest.