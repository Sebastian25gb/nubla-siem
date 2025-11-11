# Arquitectura General del Flujo de Logs

## Objetivo
Proveer un pipeline robusto, validado y extensible para ingestión de eventos de seguridad / sistema con:
- Desacoplamiento productor–almacenamiento.
- Validación temprana de calidad.
- Indexación eficiente en OpenSearch con rotación y retención.
- Base para enriquecimientos futuros (GeoIP, ECS, alertas).

## Diagrama de Alto Nivel

```mermaid
flowchart LR
    P[Productor (publish_test_message.py / futuros agentes)] --> Q[RabbitMQ Queue: nubla_logs_default]
    Q --> C[Consumer Python]
    C -->|válido| A[Alias OpenSearch: logs-default]
    C -->|inválido| DLQ[Dead Letter Queue: logs_siem.dlq]
    A --> IDX[(Índices versionados: logs-default-00000N)]
    IDX --> SR[Search / Query / Dashboards]
```

### ASCII (alternativa)
```
+-----------+        +------------------+        +-----------+        +----------------------------+
| Productor |  --->  | RabbitMQ Queue   |  --->  | Consumer  |  --->  | OpenSearch Alias logs-default |
+-----------+        | nubla_logs_default|       +-----------+        +----------------------------+
                           |                                | validados
                           |                                v
                           |                        +------------------------+
                           |                        | Índices: logs-default-00000N |
                           |                                ^
                           |                                |
                           +----> DLQ (logs_siem.dlq) <------+
                                    inválidos
```

## Papel de Cada Componente

| Componente | Rol Primario | Beneficios | Riesgo si falta |
|------------|--------------|-----------|------------------|
| Productores | Generan eventos en JSON | Escalado horizontal | No hay datos |
| RabbitMQ | Buffer (desacople), resiliencia | Absorbe picos, evita pérdida si ES lento | Bloqueo productores |
| Consumer | Normaliza, completa campos, valida, indexa | Garantiza calidad y estructura | Datos sucios en almacenamiento |
| OpenSearch Alias | Punto único de escritura | Rollover transparente | Reconfiguración manual de índices |
| Índices Versionados | Segmentación temporal/volumen | Retención y optimización selectiva | Crecimiento descontrolado |
| Pipeline de ingest | Normalización tardía (@timestamp) | Consistencia universal | Duplicación / incoherencias |
| Template de índice | Mappings uniformes | Búsquedas eficientes | Mapeos dinámicos impredecibles |
| ISM Policy | Ciclo de vida (rollover / delete) | Control de crecimiento | Saturación de disco |
| DLQ | Observabilidad de errores | Análisis y re-procesos | Dificultad de debugging |

## Principios Adoptados

1. “Validar antes de almacenar”: Menos costo que limpiar después.
2. “Alias como capa de abstracción”: Rollover sin cambios en productores.
3. “Estandarización mínima”: `@timestamp`, `tenant_id`, `severity`, `dataset`, `schema_version`, `message`.
4. “Extensibilidad futura”: Pipeline preparado para sumar procesadores (geoip, parseo).
5. “Versionado incremental de índices”: logs-default-000001, 000002, etc.

## Ciclo de Vida del Documento

1. Se publica JSON.
2. Consumer:
   - Normaliza y completa.
   - Valida.
   - Indexa vía alias con pipeline.
3. OpenSearch:
   - Aplica pipeline.
   - Guarda en índice físico actual (is_write_index true).
4. ISM (cuando corresponde):
   - Evalúa condiciones → genera nuevo índice → alias cambia.
5. Documentos antiguos:
   - Permanecen para búsqueda; serán eliminados al cumplir política (estado delete).