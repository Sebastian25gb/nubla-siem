# Operación y Troubleshooting

## Pruebas locales
- Ejecuta `pytest -m "not integration"` desde la raíz del repo.
- Si ves `ModuleNotFoundError: backend`, confirma `pythonpath = ["."]` en `pyproject.toml`.

## Tests de integraciòn RabbitMQ
- Por defecto están omitidos.
- Para correrlos: `RUN_RABBIT_INTEGRATION=true pytest -m integration -vv`.
- Consumo one-shot: añade `RUN_RABBIT_CONSUME_ONE=true`.

## OpenSearch
- Variable `OPENSEARCH_HOST` (default `opensearch:9200`).
- Salud: `curl http://localhost:9201/_cluster/health`.

## Esquema NCS
- Fichero: `backend/app/schema/ncs_v1.0.0.json`.
- Override: `NCS_SCHEMA_LOCAL_PATH`.

## Problemas comunes
- `validation_failed`: revisar severidad (ahora se mapean error→critical, alert→info, warn/warning→medium).
- Crecimiento DLQ: validar schema y tipos numéricos.

## Diff schema vs mapping
```bash
python scripts/diagnostics/check_mappings_vs_schema.py --index logs-default --host http://localhost:9201
```
Interpretación:
- missing_in_mapping: campos del schema ausentes en mapping.
- extra_in_mapping: campos sólo en mapping.
- type_mismatches: tipos distintos.

## Bulk ingest
Variables:
- USE_BULK=true/false
- BULK_MAX_ITEMS (ej. 500)
- BULK_MAX_INTERVAL_MS (ej. 1000)
- CONSUMER_PREFETCH (ej. 10 con bulk)

Métricas nuevas:
- index_latency_seconds (histogram)
- consumer_buffer_size (gauge)
- bulk_flushes_total (counter)

Flush ocurre si tamaño >= BULK_MAX_ITEMS o tiempo desde último flush >= BULK_MAX_INTERVAL_MS.

Consideraciones:
- Con USE_BULK=true se hace ack tras agregar al buffer (pequeño riesgo si container cae antes del flush).
- Ajustar prefetch según throughput (prefetch alto mejora performance pero aumenta riesgo en crash).