# Métricas y SLOs

## Métricas clave (etiquetadas por tenant_id y dataset)
- events_ingested_total
- parse_errors_total
- dlq_messages_total
- ingest_latency_seconds (p50/p95/p99)
- queue_lag_records / topic_lag_records
- storage_bytes_total (por índice/tenant)
- query_rate, query_latency_seconds (p50/p95)
- rules_fired_total, anomalies_detected_total
- cost_estimate_storage_gb (derivada)

## Objetivos (SLOs iniciales)
- p95 ingest→index ≤ 5 s a 10k EPS.
- parse_errors_total / events_ingested_total ≤ 1%.
- query_latency p95 ≤ 2 s en 24h de datos con filtros por tenant/dataset.
- disponibilidad (uptime) ≥ 99.5% (MVP) y ≥ 99.9% (Beta/Prod).

## Alertas operativas
- Aumento brusco de parse_errors_total por fuente/tenant.
- Lag sostenido > umbral por partición/tenant.
- Crecimiento anómalo de storage_bytes_total por tenant.
- Disminución de detections o ausencia súbita (pipeline roto).