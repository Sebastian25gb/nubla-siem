```markdown
# Ingest Pipeline: logs_ingest

Pipeline aplicado durante la indexación (`pipeline="logs_ingest"`).

Objetivos iniciales:
- Asegurar `severity='info'` si no viene definido.
- Espacio para procesadores futuros (geoip, threat intel).

Script de creación y validación:
  scripts/setup_ingest_pipeline.py

Ejemplos:
  OPENSEARCH_HOST=localhost:9201 python scripts/setup_ingest_pipeline.py
  OPENSEARCH_HOST=localhost:9201 python scripts/setup_ingest_pipeline.py --force
  OPENSEARCH_HOST=localhost:9201 python scripts/setup_ingest_pipeline.py --test '{"message":"demo","tenant_id":"acme"}'

Futuras mejoras:
- Añadir procesadores de limpieza de campos.
- Versionado del pipeline (logs_ingest_v2).
```