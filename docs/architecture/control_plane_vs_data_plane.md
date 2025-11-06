# Control plane vs Data plane

## Data plane (logs)
- Almacenamiento: OpenSearch.
- Unidad: documento JSON con tenant_id.
- Aislamiento: índices/data streams por tenant.
- Retención: ISM por tenant; archivo S3/Parquet.
- Analítica histórica opcional: ClickHouse (columnar), tablas particionadas por tenant/fecha.

## Control plane (identidad, permisos, configuración)
- Almacenamiento: PostgreSQL (relacional).
- Identidad: OIDC (Keycloak/Okta/Azure AD). Nubla guarda perfil mínimo y relaciones; contraseñas en IdP (o hash seguro si first‑party).
- Membresía y roles: usuario↔tenant↔rol.
- Ingesta: API keys por tenant (sólo hash; rotación/expiración).
- Config por tenant: reglas, dashboards, playbooks, conectores, cuotas.
- Auditoría: acciones administrativas y cambios de configuración.