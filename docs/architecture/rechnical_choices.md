# Decisiones técnicas y alternativas

## Estado objetivo (“all‑in”)
- Mensajería: Redpanda (API Kafka) con TLS/SASL y Schema Registry.
- Almacenamiento: OpenSearch (con Security Plugin y OIDC).
- Agentes: Vector como predeterminado (mantener Fluentd sólo si es imprescindible).
- Esquema: Nubla Common Schema (NCS) basado en ECS; validación en Schema Registry.
- Multitenencia: índices/data streams por tenant; RBAC por patrón; filtros forzados en backend.

## Razonamiento (seguridad, escalabilidad, compatibilidad, modularidad)
- Redpanda: particiones para escala, retención/replay nativos, ecosistema Kafka (Flink/Streams), schemas versionados; facilita detecciones stateful y ML.
- OpenSearch: seguridad nativa sin coste adicional; alta compatibilidad con DSL/clients de ES; ISM para ciclo de vida y costes; RBAC por índice.
- Vector: alto rendimiento, baja huella, VRL para transformaciones tempranas; amplia compatibilidad de sinks.
- NCS/ECS: reduce fricción en normalización, detección y consultas; favorece compatibilidad con herramientas del ecosistema.

## Alternativas consideradas
- RabbitMQ: simple y robusto para patrones AMQP; limitado para replays/particionado masivo y ecosistema de stream processing.
- Elasticsearch: potente, pero licenciamiento y features de seguridad avanzadas bajo suscripción.
- Fluent Bit: opción ligera; Vector ofrece VRL y pipeline más potente, preferido como default.
- Sin Schema Registry: aumenta riesgo de roturas por cambio de esquema; se descarta.

## Rutas de migración (desde el estado actual)
- Mensajería: reemplazo directo a Redpanda (proyecto en etapa temprana, menor impacto en usuarios).
- Almacenamiento: reemplazo directo a OpenSearch; validar plantillas y queries estándar.
- Agentes: introducir Vector en nuevas fuentes; coexistencia breve con Fluentd si existe.