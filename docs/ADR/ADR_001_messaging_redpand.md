# ADR-001: Mensajería — adoptar Redpanda (API Kafka)

## Contexto
Se requiere mensajería con alta escala, retención y replays, y compatibilidad con stream processing (Flink/Kafka Streams) y Schema Registry.

## Decisión
Adoptar Redpanda como bus de eventos (API Kafka), con TLS/SASL y ACLs.

## Alternativas
- RabbitMQ (AMQP): simple y robusto; limitado para replays/particionado masivo y ecosistema Kafka.
- Kafka clásico: más complejo de operar (Zookeeper).

## Consecuencias
- Cambia el paradigma (exchanges/colas → topics/particiones).
- Permite particionado por tenant/entidad, replays y mayor throughput.
- Facilita la introducción de Flink y validación de schemas.