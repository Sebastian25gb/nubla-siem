# Glosario

| Término | Definición |
|---------|------------|
| Alias | Nombre lógico que apunta a uno o más índices físicos. |
| Write Index | Índice físico donde el alias escribe nuevos documentos. |
| Rollover | Proceso de creación de un nuevo índice y actualización del alias. |
| ISM | Index State Management: motor de políticas de ciclo de vida. |
| DLQ | Dead Letter Queue: cola de mensajes rechazados. |
| Pipeline | Conjunto de procesadores de ingest aplicada antes de indexar. |
| Template | Definición de settings y mappings para nuevos índices que coincidan con un patrón. |
| Normalización | Ajuste de evento para cumplir estructura esperada (nombres de campo, tipos). |
| Validación | Comprobación contra un JSON Schema definido. |
| schema_version | Etiqueta semántica que indica versión del contrato de datos. |
| dataset | Identifica la fuente lógica/funcional del evento (ej. syslog.generic). |
| severity | Nivel de importancia de un evento. |
| @timestamp | Marca de tiempo normalizada (ISO8601 UTC). |