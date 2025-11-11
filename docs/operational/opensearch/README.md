# OpenSearch Operational Assets

Este directorio contiene artefactos para asegurar ingest consistente y manejo del ciclo de vida de índices de logs.

## Archivos

- `pipeline_ensure_at_timestamp.json`: Ingest pipeline que garantiza @timestamp y elimina `timestamp`.
- `index_template_logs.json`: Template para índices `logs-*` con mappings y pipeline por defecto, e incluye la setting `index.opendistro.index_state_management.rollover_alias`.
- `ism_policy_logs-default.json`: Política ISM (rollover + delete) para índices `logs-default-*`, con `ism_template` para aplicar automáticamente.
- `setup.sh`: Script idempotente que instala/actualiza pipeline, template y política; crea índice base, fija la setting `rollover_alias` en el write index y hace un rollover de prueba (dry-run).

## Uso rápido

```bash
cd docs/operational/opensearch
bash setup.sh http://localhost:9201
```

## Notas

- El alias de escritura debe llamarse `logs-default` y apuntar al índice `logs-default-000001` inicialmente.
- Requisito ISM: cada índice gestionado debe tener la setting `index.opendistro.index_state_management.rollover_alias` con el valor `logs-default`. El `setup.sh` la establece en el write index actual y el template la hereda para futuros índices.
- Rollover manual (real): `POST /logs-default/_rollover` con header `Content-Type: application/json`.
- ISM evalúa periódicamente; `explain` puede tardar unos minutos en reflejar estado.