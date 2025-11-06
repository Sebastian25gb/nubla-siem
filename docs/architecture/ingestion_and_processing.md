# Ingesta y procesamiento

## Flujo objetivo
1. Agentes/entradas (Vector, otros) envían eventos con token/mTLS.
2. Gateway valida identidad del tenant y adjunta tenant_id + schema_version.
3. Publicación en Redpanda:
   - Topic logs.v1 (clave de partición: hash(tenant_id + entidad)).
   - Headers con tenant_id, dataset.
4. Validación y normalización:
   - Validación contra Schema Registry (NCS v1).
   - Normalización/enriquecimiento (GeoIP/ASN/Threat Intel).
5. Persistencia:
   - Resolución de alias por tenant/dataset.
   - Indexación en OpenSearch con ISM por tenant.
6. Detección:
   - Reglas (Sigma→DSL/stream) y anomalías (v1 simple, luego stream stateful).
7. Automatización (SOAR‑lite):
   - Publicación de alertas (detections.v1).
   - Ejecución de playbooks con aprobaciones.

## DLQ
- Eventos inválidos o con errores graves → dlq.v1 con causa.
- Herramienta de inspección y replay por tenant.

## Esquema y contratos
- NCS v1 (ECS‑based) como contrato único; versionado y compatible hacia atrás.
- Cambios de schema: policy de deprecación y validación en gateway.