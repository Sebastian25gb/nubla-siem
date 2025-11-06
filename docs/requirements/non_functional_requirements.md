# Requisitos No Funcionales y SLOs

## Seguridad
- Autenticación: OIDC/OAuth2 con SSO; tokens con claims de tenant y roles.
- Autorización: RBAC por tenant; filtros forzados de tenant en backend; roles por patrón de índice en OpenSearch Security.
- Aislamiento: datos por índices/data streams por tenant; secretos segregados por entorno.
- Auditoría: accesos, cambios de configuración/reglas, ejecuciones de playbooks.

## Escalabilidad y rendimiento
- Ingesta: objetivo inicial ≥ 10k EPS sostenidos; crecimiento por particiones (tenant + entidad).
- Latencia hot path (ingesta→consulta): p95 ≤ 5 s (MVP), ≤ 3 s (Alpha), ≤ 2 s (Beta/Prod).
- Disponibilidad: SLO 99.5% (MVP), 99.9% (Beta/Prod).
- Capacidad: ISM con hot/warm/cold/frozen; rollover por tamaño/edad; archivado en objeto compatible S3.

## Compatibilidad
- Esquema de eventos basado en ECS con extensiones Nubla (NCS v1).
- Reglas compatibles con Sigma (traducción a DSL y/o stream).
- Integraciones comunes: Syslog, Windows, AWS, Azure, GCP, EDR, IAM, ticketing.

## Observabilidad
- Métricas por tenant: EPS, lag, parse_errors, dlq_total, ingest_latency.
- Logs estructurados y trazas (OpenTelemetry) en servicios clave (ingesta, normalizador, detecciones, consultas).

## SLOs iniciales
- p95 ingest→index ≤ 5 s @ 10k EPS.
- Error de parsing ≤ 1% por fuente; DLQ re‑procesable.
- Tiempo de búsqueda p95 en 24h: ≤ 2 s con filtros por tenant/dataset.