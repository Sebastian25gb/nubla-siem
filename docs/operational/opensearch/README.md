# OpenSearch Operational Assets

Este directorio contiene artefactos para asegurar ingest consistente y manejo del ciclo de vida de índices de logs.

## Archivos

- `pipeline_ensure_at_timestamp.json`: Ingest pipeline que garantiza @timestamp y elimina `timestamp`.
- `index_template_logs.json`: Template para índices `logs-*` con mappings y pipeline por defecto.
- `ism_policy_logs-default.json`: Política ISM (rollover + delete) para índices `logs-default-*`.
- `setup.sh`: Script idempotente que instala/actualiza pipeline, template y política; crea índice base y hace rollover de prueba.

## Uso rápido

```bash
cd docs/operational/opensearch
bash setup.sh http://localhost:9201
```

## Notas

- El alias de escritura debe llamarse `logs-default` y apuntar al índice `logs-default-000001` inicialmente.
- Rollover manual: `POST /logs-default/_rollover`.
- ISM evalúa periódicamente; `explain` puede tardar unos minutos en reflejar estado.