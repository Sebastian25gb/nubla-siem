# Gestión de DLQ (Dead Letter Queue)

## Principios
- Cualquier evento inválido o con error grave va a dlq.v1 con causa y metadatos (tenant_id, dataset, schema_version).
- No se pierden eventos: se inspeccionan, clasifican y, si procede, se re‑procesan.

## Flujo operativo
1. Monitoreo: alertas por incremento de dlq_messages_total por tenant/fuente.
2. Inspección: muestras de DLQ para identificar causas (schema, parsing, datos corruptos).
3. Corrección: actualizar schema, parser o configuración de fuente.
4. Replay: re‑publicar en logs.v1 los eventos corregidos, por tenant y ventana de tiempo.
5. Cierre: documentar incidente y lecciones; ajustar validaciones si procede.

## Buenas prácticas
- Añadir códigos de error normalizados en DLQ.
- Limitar retención de DLQ (operativa) y exportar a archivo si fuese necesario.
- Evitar replays masivos sin tasa controlada (throttling).