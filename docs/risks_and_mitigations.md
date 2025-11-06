# Riesgos y mitigaciones

- Fuga cross‑tenant
  - Mitigación: filtros forzados en backend; roles por patrón en OpenSearch; pruebas de acceso cruzado; auditoría.
- Costes por cardinalidad en OpenSearch
  - Mitigación: mappings correctos (keyword vs text), ISM/tiering, límites de campos dinámicos, ClickHouse para históricos.
- Complejidad operativa Kafka/Flink
  - Mitigación: Redpanda (sin ZK), introducir stream processing gradualmente; automatizar despliegues.
- Falsos positivos en IA
  - Mitigación: métodos simples primero, feedback humano, monitoreo de drift y retraining.
- Calidad de datos y parsers
  - Mitigación: Schema Registry, validación temprana, DLQ con herramientas de inspección/replay por tenant.
- Dependencia de LLM para NLP
  - Mitigación: AST/guardrails, fallback a query builder, modelos on‑prem, límites de recursos y cuotas.
- Noisy neighbor
  - Mitigación: quotas por tenant (EPS/almacenamiento/queries), rate limiting, priorización y alertas.