# ADR-005: Multitenencia — índices por tenant

## Contexto
Se requiere aislamiento fuerte de datos, control de retención y costes por tenant.

## Decisión
Separar datos por índices/data streams por tenant (y opcionalmente por dataset), con ISM y roles por patrón.

## Alternativas
- Un único índice con campo tenant_id: seguridad más débil, retención común, cardinalidad elevada.

## Consecuencias
- Aislamiento nativo y sencillo de aplicar con RBAC.
- Configuración de retención y recursos por tenant.