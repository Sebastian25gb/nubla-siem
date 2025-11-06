# Nubla SIEM — Visión y Alcance

## Visión
Construir un SIEM multi‑tenant de alto rendimiento que compita con Splunk, incorporando IA para detección, consulta en lenguaje natural y automatización, manteniendo costes y complejidad bajo control mediante arquitectura modular, estándares abiertos y eficiencias en almacenamiento y procesamiento.

## Principios rectores
- Seguridad primero: aislamiento fuerte por tenant, mínimos privilegios, cifrado, auditoría.
- Escalabilidad horizontal: componentes distribuidos, separación hot/warm/cold, particionado por tenant y entidad.
- Compatibilidad: estándares (ECS/Sigma/OIDC/OTel), APIs limpias, esquemas versionados.
- Modularidad: servicios con límites claros; contratos de eventos y almacenamiento desacoplado.
- Evolución disciplinada: fijar arquitectura objetivo temprano y avanzar por capas con validación continua.

## Alcance (MVP → Beta → Producción)
- MVP: ingesta multi‑fuente, normalización a esquema común, almacenamiento searchable, detecciones por reglas, multitenencia inicial con índices por tenant y RBAC, observabilidad básica.
- Beta: stream processing, IA (anomalías v1), NLP (alpha), SOAR‑lite, cuotas por tenant, tiering de almacenamiento.
- Producción: seguridad endurecida (TLS end‑to‑end, OIDC, auditoría completa), HA/DR, optimización de costes (ISM, S3/Parquet, posible ClickHouse), onboarding de múltiples tenants.