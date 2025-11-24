```markdown
# Ingest Pipeline: logs_ingest

Pipeline básico aplicado en indexación (`pipeline="logs_ingest"`).
Propósito inicial:
- Garantizar `severity` si falta.
- Espacio para posteriores enriquecimientos (geoip, threat intel, normalización extendida).

Script de creación: `scripts/setup_ingest_pipeline.py`
Uso:
  OPENSEARCH_HOST=localhost:9201 python scripts/setup_ingest_pipeline.py
  OPENSEARCH_HOST=localhost:9201 python scripts/setup_ingest_pipeline.py --force
  OPENSEARCH_HOST=localhost:9201 python scripts/setup_ingest_pipeline.py --test '{"message":"demo","tenant_id":"acme"}'

Recomendaciones futuras:
- Añadir geoip (cuando plugin de ingest vuelva a estar habilitado).
- Añadir normalización de campos categóricos.
- Control de versiones del pipeline (ej: logs_ingest_v2).