# Validación y Dead Letter Queue (DLQ)

## Propósito
Evitar contaminación del almacenamiento con eventos incompletos o mal formados y preservar trazabilidad de fallos.

## Proceso de Validación

1. Consumer completa:
   - `@timestamp` (copiar `timestamp` o generar).
   - `dataset` (default).
   - `schema_version` (default).
2. Aplica JSON Schema local.
3. Si errores:
   - Log: `validation_failed`.
   - NACK: `basic_nack(requeue=False)`.
   - Mensaje termina en `logs_siem.dlq`.

## Campos Críticos de Rechazo
| Campo | Motivo frecuente |
|-------|------------------|
| @timestamp | No string ISO |
| severity | Null o fuera de enumeración |
| message | Faltante |
| dataset | Faltante |
| schema_version | Faltante |

## Consulta de Eventos Válidos
```bash
curl -sS -X POST 'http://localhost:9201/logs-default-00000X/_search' \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match":{"severity":"critical"}}, "size":10}' | jq '.hits.hits[]._source'
```

## Consulta de DLQ (RabbitMQ)
```bash
docker-compose exec rabbitmq rabbitmqctl list_queues name messages | grep logs_siem.dlq
```

## Reprocesamiento Manual (Futuro)
1. Consumir mensajes de DLQ mediante script AMQP.
2. Aplicar correcciones (p.ej. completar severity).
3. Republicar a `nubla_logs_default`.

## Buenas Prácticas
- Registrar ratio `validation_failed / event_indexed`.
- Mantener schema versionado en el repositorio (control de cambios).
- Introducir nuevos campos como opcionales primero.
