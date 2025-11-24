### Modos de ejecución (Host vs Docker)

| Aspecto        | Host (venv)                      | Docker (contenedor backend)          |
|----------------|----------------------------------|--------------------------------------|
| RABBITMQ_HOST  | 127.0.0.1                        | rabbitmq                             |
| ELASTICSEARCH_HOST / OpenSearch | 127.0.0.1:9201             | opensearch:9200                      |
| Schema path    | backend/app/schema/ncs_schema_registry.json (o ruta absoluta) | igual dentro del contenedor |
| Pipeline logs_ingest | Pre-creado vía API en host | Pre-creado vía docker-compose init (pendiente) |
| Ejecución consumer | `python -m backend.app.processing.consumer` | `docker compose run --rm backend python -m backend.app.processing.consumer` |

Para cambiar de modo:
1. Ajustar .env a los hostnames adecuados.
2. Verificar que puertos (5672, 9201) estén publicados si se usa Host.
3. Reaplicar template y pipeline si se recrea OpenSearch.

### Smoke test

Ejecutar:
```
python scripts/integration/smoke_pipeline.py
```
Criterios:
- `severity_lowercase: true`
- `invalid_in_dlq: true`
- `pass: true`
```markdown
### Nuevas métricas (Commit 3)

- normalizer_latency_seconds: tiempo de normalización por evento.
- tenant_registry_size: número de tenants cargados.
- bulk_errors_total: errores o partial errors en flush bulk.
- os_index_retry (log): un intento de reintento de indexación.
- os_index_failed_final (log): fallo definitivo tras agotar reintentos.
```