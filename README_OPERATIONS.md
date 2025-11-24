# Operaciones: Rollover de índices por tenant

Este repositorio indexa en índices por tenant con alias `logs-<tenant>`. El script `scripts/rollover_tenant_index.py` automatiza:
- Inicialización del primer índice y alias (`logs-<tenant>-000001` + alias `logs-<tenant>` con `is_write_index: true`)
- Rollover con condiciones (`max_docs`, `max_size`, `max_age`), opcionalmente en `--dry-run`

Requisitos:
- OpenSearch accesible (por defecto `http://opensearch:9200`, configurable con `OPENSEARCH_HOST`)
- Python con `opensearch-py` instalado (ya está en requirements)

## Comandos básicos

Inicializar alias/índice si no existen:
```bash
python scripts/rollover_tenant_index.py --tenant delawarehotel --init --shards 1 --replicas 0
```

Ver estado actual:
```bash
python scripts/rollover_tenant_index.py --tenant delawarehotel --check
```

Simular rollover (no crea índice):
```bash
python scripts/rollover_tenant_index.py --tenant delawarehotel --rollover --dry-run --max-docs 1000000 --max-size 50gb --max-age 7d
```

Ejecutar rollover real:
```bash
python scripts/rollover_tenant_index.py --tenant delawarehotel --rollover --max-docs 1000000 --max-size 50gb --max-age 7d
```

Notas:
- El script asegura `is_write_index: true` en el índice de escritura del alias.
- Si el alias existe sin `is_write_index`, lo corrige.
- Los índices siguen el patrón `logs-<tenant>-000001`, `logs-<tenant>-000002`, ...

## Sugerencia de automatización (cron)

Ejemplo de cron diario con dry-run (solo simula y loguea):
```cron
0 2 * * * cd /srv/nubla-siem && /usr/bin/python3 scripts/rollover_tenant_index.py --tenant delawarehotel --rollover --dry-run --max-docs 15000000 --max-size 50gb --max-age 7d >> /var/log/nubla/rollover.log 2>&1
```

Y un job semanal real:
```cron
0 3 * * 0 cd /srv/nubla-siem && /usr/bin/python3 scripts/rollover_tenant_index.py --tenant delawarehotel --rollover --max-docs 15000000 --max-size 50gb --max-age 7d >> /var/log/nubla/rollover.log 2>&1
```

## Troubleshooting

- 404 alias not found:
  - Ejecuta `--init` antes del rollover.
- `is_write_index` ausente:
  - El script lo corrige mediante `update_aliases`.
- Permisos / autenticación:
  - Usa `OS_USER/OS_PASS` o `ES_USER/ES_PASS`.
- Validación previa:
  - Usa `--dry-run` para ver si las condiciones gatillarían un rollover sin crear índices.

## Variables de entorno relevantes

- `OPENSEARCH_HOST` (o `ELASTICSEARCH_HOST`): host:puerto o URL completa
- `OS_USER`/`OS_PASS` (o `ES_USER`/`ES_PASS`): credenciales
- `ROLLOVER_SHARDS`/`ROLLOVER_REPLICAS`: valores por defecto para `--shards` y `--replicas`