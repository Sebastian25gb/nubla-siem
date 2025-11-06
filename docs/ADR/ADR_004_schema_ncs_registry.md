# ADR-004: Esquema — NCS (ECS-based) + Schema Registry

## Contexto
Es crítico estandarizar eventos y evitar roturas por cambios de schema.

## Decisión
Adoptar Nubla Common Schema (NCS) basado en ECS, versionado y validado con Schema Registry (JSON Schema inicialmente).

## Alternativas
- Schemas ad-hoc por fuente: aumentan acoplamiento y fragilidad.

## Consecuencias
- Validación temprana; eventos inválidos a DLQ con causa.
- Evolución controlada del schema con compatibilidad backward.