# Operación y Troubleshooting

## Pruebas locales
- Ejecuta `pytest -m "not integration"` desde la raíz del repo.
- Si ves `ModuleNotFoundError: backend`, confirma `pythonpath = ["."]` en `pyproject.toml`.

## Tests de integración RabbitMQ
- Por defecto están omitidos.
- Para correrlos: `RUN_RABBIT_INTEGRATION=true pytest -m integration -vv`.
- Consumo one-shot: añade `RUN_RABBIT_CONSUME_ONE=true`.

## OpenSearch
- Variable `OPENSEARCH_HOST` o `settings.opensearch_host` (default `opensearch:9200`).
- Verifica salud: `curl http://localhost:9201/_cluster/health`.

## Esquema NCS
- Fichero: `backend/app/schema/ncs_v1.0.0.json`.
- Env override: `NCS_SCHEMA_LOCAL_PATH`.

## Problemas comunes
- Rechazos por schema: revisar logs `validation_failed` y headers `x-reject-reason` en DLQ.
- DLQ creciente: validar mapeos vs schema y severidad en minúsculas.