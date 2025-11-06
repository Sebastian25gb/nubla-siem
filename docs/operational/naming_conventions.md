# Convenciones de nombres

## Topics (Redpanda)
- logs.v1            — eventos de log validados (payload en NCS v1).
- dlq.v1             — eventos rechazados con metadatos de error.
- detections.v1      — eventos de detección/alerta.
- playbooks.v1       — orquestación de acciones.

Claves de partición:
- hash(tenant_id + entidad_principal) para locality y orden por entidad.

Headers comunes:
- tenant_id, dataset, schema_version.

## Índices (OpenSearch)
- Por tenant:
  - logs-<tenant>-YYYY.MM.DD (agrupado), o
  - logs-<tenant>-<dataset>-YYYY.MM.DD (granular).
- Alias de escritura:
  - logs-<tenant>-write, o logs-<tenant>-<dataset>-write.
- Plantillas y políticas ISM con nombres por tenant:
  - template-logs-<tenant>[-<dataset>], ism-logs-<tenant>.

## Datasets
- vendor.product o fuente lógica:
  - fortinet.fortigate, windows.security, aws.cloudtrail, o365.audit, okta.system, github.audit.