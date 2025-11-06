# Estado actual y plan delta

## Estado inicial (resumen)
- Ingesta: Fluentd → RabbitMQ (exchange + DLX + DLQ) → consumidor Python → Elasticsearch.
- API: FastAPI con /health y /metrics.
- Orquestación: docker-compose.
- Normalización: parser Fortinet KV, enriquecimiento mínimo.

## Decisiones “all‑in” (objetivo)
- Redpanda (Kafka API) en mensajería, con Schema Registry.
- OpenSearch como almacenamiento principal con Security y OIDC.
- Vector como agente recomendado para nuevas fuentes.
- NCS (ECS‑based) como contrato de eventos y validación temprana.

## Cambios clave
- AMQP→Kafka: topics y particiones; offsets y consumer groups.
- ES→OpenSearch: ISM, roles por patrón, OIDC.
- Fluentd→Vector (progresivo): transformaciones tempranas (tenant/dataset).
- DLQ unificado (topic) con inspección y replay.

## Acciones inmediatas (documentación y diseño)
- Publicar NCS v1 y su política de versionado/compatibilidad.
- Definir naming (topics, índices, datasets) y SLOs.
- Preparar checklists de bootstrap (Redpanda/OpenSearch).
- Diseñar RBAC por tenant y filtros forzados en backend (especificación).