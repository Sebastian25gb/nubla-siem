# Diseño de multitenencia

## Principios
- Tenant como primer ciudadano: presente en cada evento, métrica, permiso y recurso.
- Aislamiento de datos, configuración (reglas, dashboards, playbooks) y recursos (quotas).

## Identificación de tenant en ingesta
- Métodos soportados (coexistentes):
  - Token por tenant (recomendado MVP): validado en gateway.
  - Listener/puerto dedicado por tenant (operativo para legacy).
  - mTLS con mapeo CN/OU→tenant (opción enterprise).
- Fallback por IP→tenant desaconsejado salvo casos muy controlados.

## Contrato de evento (NCS v1, inspirado en ECS)
- Obligatorios: tenant_id, @timestamp UTC, dataset, category, severity, message, schema_version.
- Recomendados: source/destination.*, user.*, labels, original.
- Política: eventos sin tenant_id válido → rechazo y envío a DLQ con causa.

## Aislamiento de datos
- Índices/data streams por tenant (y opcionalmente por dataset).
- ISM por tenant (retención, replicas, rollover).
- Seguridad nativa: roles por patrón de índice en OpenSearch Security.

## Control de acceso
- OIDC: tokens con claims de tenant y roles.
- Backend: filtros forzados y auditoría por solicitud; scoping estricto por tenant.
- Roles: owner/admin/analyst/viewer a nivel de tenant.

## Quotas y límites
- Ingesta: EPS máximo por tenant (control en gateway y monitorización).
- Almacenamiento: cuota por tenant; retención configurada por SLA.
- Consultas: límites de cardinalidad/tiempo y rate limits por tenant.

## Observabilidad por tenant
- Métricas etiquetadas: events_ingested_total, parse_errors_total, dlq_messages_total, ingest_latency p95, storage_bytes.
- Dashboards: salud del pipeline por tenant; top fuentes ruidosas; costos estimados.

## Operaciones
- DLQ: inspección/replay filtrado por tenant; informes de calidad de datos.
- Exportación: export de índices por tenant para portabilidad/cumplimiento.