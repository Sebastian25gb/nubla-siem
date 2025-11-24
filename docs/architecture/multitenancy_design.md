```markdown
# Multitenencia – Diseño Inicial

## Objetivo
Asegurar aislamiento lógico de eventos por cliente (tenant) y evitar contaminación cruzada de datos.

## Estrategia de Índices
- Índice por tenant: `logs-<tenant>` (alias/rollover opcional en producción).
- Consumer escribe en `logs-<tenant>`.

## Validación
- `tenant_id` obligatorio en cada evento.
- Si falta → rechazo (`missing_tenant_id`) vía DLQ manual o NACK sin requeue.
- No se autocompleta `tenant_id=default` en normalizador; solo se acepta si viene del productor.

## Métricas
- `events_indexed_by_tenant_total{tenant_id="x"}`
- `events_nacked_by_reason_total{reason="missing_tenant_id"}`

## Próximos pasos
1. Añadir tabla de tenants válidos y verificación (unknown_tenant_id).
2. Script de creación de índices/alias por tenant.
3. Revisión de RBAC/roles en OpenSearch por tenant.
```