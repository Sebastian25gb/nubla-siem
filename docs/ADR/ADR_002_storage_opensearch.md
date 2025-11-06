# ADR-002: Almacenamiento — adoptar OpenSearch

## Contexto
Se necesita búsqueda/analítica de logs con seguridad nativa, RBAC por patrón y control de ciclo de vida.

## Decisión
Adoptar OpenSearch (con Security Plugin y OIDC) como datastore principal de logs.

## Alternativas
- Elasticsearch (licenciamiento y features avanzadas bajo suscripción).
- ClickHouse (excelente para agregados; no reemplaza búsquedas full-text).

## Consecuencias
- Compatibilidad alta con DSL y clientes de ES.
- Uso de ISM para retención/tiering por tenant.
- RBAC por patrón de índice y auditoría integrada.