# Exporter de Métricas (OpenSearch)

Exporter HTTP ligero que expone métricas para Prometheus, consultando OpenSearch por alias.

## Archivo
- `docs/operational/metrics/exporter.py`

## Variables
- `OS_URL` (por defecto `http://localhost:9201`)
- `LOGS_ALIAS` (por defecto `logs-default`)
- `PORT` (por defecto `9108`)

## Ejecución
```bash
OS_URL=http://localhost:9201 LOGS_ALIAS=logs-default PORT=9108 \
python docs/operational/metrics/exporter.py
```

## Endpoints
- `GET /metrics` → formato Prometheus text

## Métricas expuestas
- `nubla_logs_docs_total{alias}`
- `nubla_logs_docs_severity{alias,severity}`
- `nubla_logs_docs_last_hour{alias}`