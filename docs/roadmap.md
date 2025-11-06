# Roadmap (sin fechas)

## Épica A — Plataforma base “all‑in”
- Redpanda + Schema Registry; OpenSearch + Security + OIDC; Vector como agente recomendado.
- NCS v1 publicado y validación de schemas en entrada.

## Épica B — Multitenencia estricta
- Roles y patrones de índice por tenant; filtros forzados en backend; métricas etiquetadas.
- Quotas por tenant (EPS, almacenamiento, queries).

## Épica C — Pipeline de normalización y DLQ
- Normalización a NCS; enriquecimiento básico; DLQ operable con inspección/replay por tenant.

## Épica D — Motor de reglas (Sigma)
- Traducción Sigma→DSL (OpenSearch) y primeros casos (brute force, escaneo).
- UI/CRUD de reglas por tenant; supresión/deduplicación.

## Épica E — Anomalías v1
- Detecciones no supervisadas (z‑score/Isolation Forest) por entidad; telemetría TPR/FPR; feedback de analistas.

## Épica F — NLP (alpha)
- NL→AST→DSL con guardrails y RAG sobre NCS; conjunto de pruebas.

## Épica G — SOAR‑lite
- Playbooks con aprobaciones y conectores clave; auditoría completa y dry‑run.

## Épica H — Escala y costos
- S3/Parquet para archivo; posible ClickHouse para históricos; políticas de cardinalidad y sampling.