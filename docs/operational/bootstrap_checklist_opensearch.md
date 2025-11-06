# Checklist de bootstrap — OpenSearch

1) Seguridad y OIDC
- Habilitar Security Plugin.
- Integrar OIDC (Keycloak/Okta/Azure AD); mapear roles.
- Definir roles por patrón de índice (logs-<tenant>-*), field/document-level si aplica.

2) Índices y plantillas
- Publicar index templates basados en NCS/ECS (mappings y settings).
- Configurar ISM por tenant (hot/warm/cold/frozen, rollover).
- Definir aliases de escritura por tenant/dataset.

3) Observabilidad
- Health del cluster, shards/replicas, heap/GC, query latency.
- Dashboards por tenant (tamaño de índices, ingest rate).

4) Backup y DR
- Repositorio de snapshots (objeto compatible S3).
- Política de snapshots y verificación periódica de restores.

5) Operación
- Procedimientos para cambio de ISM por tenant.
- Controles de cardinalidad (campos peligrosos, dynamic mappings).