# Runbook Operacional de Logging

## Objetivo
Guía rápida para operar, diagnosticar y mantener el pipeline de ingestión de logs.

## Comandos Clave

### Publicar evento de prueba
```bash
RABBITMQ_HOST=localhost RABBITMQ_QUEUE=nubla_logs_default python backend/app/tools/publish_test_message.py
```

### Ver eventos indexados recientes
```bash
curl -sS -X POST 'http://localhost:9201/logs-default-00000X/_search' \
  -H 'Content-Type: application/json' \
  -d '{"size":5,"sort":[{"@timestamp":{"order":"desc"}}]}' | jq '.hits.hits[]._source'
```

### Ver errores de validación en consumer
```bash
docker-compose logs --tail=200 backend-consumer | grep -E 'validation_failed|processing_failed|event_indexed'
```

### Ver cola DLQ (requiere management API o rabbitmqctl)
```bash
docker-compose exec rabbitmq rabbitmqctl list_queues name messages | grep logs_siem.dlq
```

## Escenarios Comunes

| Síntoma | Causa | Acción |
|---------|-------|--------|
| No aparece event_indexed | Evento inválido | Revisar `validation_failed` logs |
| 406 en rollover | Falta Content-Type | Añadir `-H 'Content-Type: application/json'` |
| ISM ‘Missing rollover_alias’ | Setting ausente | Añadir setting en índice write |
| Documentos con campo `timestamp` duplicado | Pipeline incompleto | Reaplicar pipeline ensure_at_timestamp |
| Consumer se cae | Conexión RabbitMQ | Reiniciar `docker-compose up -d --force-recreate backend-consumer` |

## Rollover Manual
```bash
curl -sS -X POST 'http://localhost:9201/logs-default/_rollover' \
  -H 'Content-Type: application/json' \
  -d '{"conditions":{"max_docs":100000}}' | jq
```

## Borrado de Índice Antiguo (tras verificación)
```bash
curl -sS -X DELETE 'http://localhost:9201/logs-default-000003' | jq
```

## Reprocesar Todos los Documentos (ej., añadir @timestamp)
```bash
curl -sS -X POST 'http://localhost:9201/logs-default-000005/_update_by_query?conflicts=proceed&pipeline=ensure_at_timestamp' \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match_all":{}}}' | jq
```

## Renovar Template
```bash
curl -sS 'http://localhost:9201/_index_template/logs_template' | jq
```

## Validar ISM
```bash
curl -sS 'http://localhost:9201/_plugins/_ism/explain/logs-default-00000X' | jq
```

## Recuperar Mensajes DLQ (re-proceso manual futuro)
1. Exportar contenido (necesitarás script que consuma la DLQ).
2. Limpiar campos.
3. Re-publicar a `nubla_logs_default`.

## Política de Retención
Definida por ISM: rollover cada ~1d/1GB/100k docs → delete tras 7d.
Ajustar si:
- Crecimiento acelerado → disminuir min_index_age.
- Demasiado granular → aumentar min_doc_count.
