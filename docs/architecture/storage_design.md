# Diseño de almacenamiento (OpenSearch) y relación logs↔tenants

## Modelo de datos (NCS/ECS)
- Documento JSON por evento con campos clave:
  - tenant_id (obligatorio), @timestamp (UTC), dataset, category, severity, message,
  - source/destination.*, user.*, labels, original, schema_version.

## Esquema de indexación
- Por tenant (recomendado):
  - logs-<tenant>-YYYY.MM.DD (agrupado) o logs-<tenant>-<dataset>-YYYY.MM.DD (granular).
  - Alias de escritura por tenant/dataset.
- Plantillas de índice compartidas (mappings ECS/NCS) con ISM por tenant.

## Ciclo de vida (ISM)
- Hot → Warm → Cold → Frozen (configurado por tenant).
- Rollover por tamaño y/o edad.
- Retención y número de réplicas alineados al SLA del tenant.

## Seguridad y acceso
- OIDC + RBAC: roles con permisos sobre patrones logs-<tenant>-*.
- Backend aplica filtros obligatorios por tenant_id y audita consultas.

## Consultas
- La UI/API opera sobre alias/patrones del tenant.
- Consultas multi‑dataset dentro del tenant sin riesgo de fuga.
- Consultas multi‑tenant deshabilitadas por defecto (roles especiales si es necesario).

## Cuotas y costes por tenant
- EPS máximo, almacenamiento máximo, límites de consulta.
- Métricas por tenant para chargeback/showback.

## Archivo y reproceso
- Archivo en objeto compatible S3 (cifrado) o export Parquet particionado por tenant y fecha.
- Reprocesos batch leen por particiones de tenant/fecha y reindexan si procede.

## Sharding y rendimiento
- Evitar oversharding: objetivo ~20–50 GB por shard.
- Réplicas ajustadas por SLA.
- Control de cardinalidad: mapear correctamente keyword/text, limitar campos de alta cardinalidad.

## DLQ por tenant
- Topic de DLQ con metadatos (tenant, error, schema_version).
- Índice operativo opcional por tenant con retención corta para inspección.