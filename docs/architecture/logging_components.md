# Componentes del Sistema de Logging

## Productores
Scripts actuales y futuros agentes:
- Publican eventos JSON a `nubla_logs_default`.
- Deben incluir: `tenant_id`, `message`, preferentemente `@timestamp`, `severity`, `dataset`, `schema_version`.

## RabbitMQ
- Cola principal: `nubla_logs_default`
- DLQ: `logs_siem.dlq`
- Ventajas: desacopla la presión del almacenamiento, permite análisis de errores.

## Consumer (backend/app/processing/consumer.py)
Responsabilidades:
- Conexión a RabbitMQ.
- Normalización (placeholder).
- Completar campos faltantes.
- Validación con schema local.
- Indexación en OpenSearch usando alias `logs-default`.

## OpenSearch
Elementos configurados:
- Ingest Pipeline: `ensure_at_timestamp`
- Index Template: `logs_template` (patrón `logs-*`)
- Alias: `logs-default`
- Índices físicos: `logs-default-00000N`
- ISM Policy: `logs-default-ism` (rollover + delete)

## Dead Letter Queue
- Almacena mensajes rechazados por validación.
- Permite auditoría y futuros reprocesos (p.ej. cuando se relaxe esquema).

## JSON Schema Local
Garantiza:
- Presencia de campos requeridos.
- Tipos correctos.
- Valores enumerados (ej: severity).

## ISM (Index State Management)
Estados:
- hot → acciones: rollover (min_doc_count / min_size / min_index_age)
- delete → acción: borrado tras `min_index_age` 7d

Requisito:
- Setting `index.opendistro.index_state_management.rollover_alias`: `logs-default`.
