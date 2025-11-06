# Plan de trabajo (entregables y criterios)

## A. Plataforma base
- Entregables: Redpanda con TLS/SASL y Registry; OpenSearch con Security/OIDC; Vector como agente; NCS v1 documentado.
- Criterios: ingest→index p95 ≤ 5 s a 10k EPS; RBAC por tenant operativo; validación de schema en entrada.

## B. Multitenencia estricta
- Entregables: roles por patrón logs-<tenant>-*; filtros forzados por tenant en backend; cuotas iniciales.
- Criterios: pruebas de acceso cruzado fallan; métricas de plataforma segmentadas por tenant.

## C. Normalización y DLQ
- Entregables: pipeline NCS, enriquecimiento básico, DLQ con inspección y replay.
- Criterios: ≥ 95% de eventos conformes a NCS v1; ratio de errores ≤ 1%.

## D. Reglas (Sigma)
- Entregables: parser Sigma→DSL y/o stream; UI/CRUD por tenant; supresión.
- Criterios: 10 reglas clave con FPR < 5% en datasets de validación.

## E. Anomalías v1
- Entregables: detecciones no supervisadas per‑tenant; almacenamiento de scores; panel de calidad.
- Criterios: 2 casos con valor probado (p. ej., brute force, exfil).

## F. NLP (alpha)
- Entregables: gramática AST, traductor a DSL, guardrails, RAG sobre NCS.
- Criterios: ≥ 70% de queries naturales convertidas correctamente en pruebas.

## G. SOAR‑lite
- Entregables: playbooks declarativos, aprobaciones, conectores (Fortinet/Okta/Jira).
- Criterios: 3 playbooks auditables y seguros (con dry‑run).

## H. Escala y costes
- Entregables: archivo S3/Parquet; evaluación/introducción de ClickHouse; controles de cardinalidad/sampling.
- Criterios: reducción ≥ 30% del coste por GB sin perder casos críticos.