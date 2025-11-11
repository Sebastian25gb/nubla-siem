# Extensiones Futuras

## Enriquecimientos
- GeoIP: Añadir processor `geoip` para `source.ip` → `source.geo.country_name`, etc.
- User-Agent parsing (si se incorporan logs HTTP).
- Normalización ECS para interoperabilidad con herramientas SIEM.

## Observabilidad
- Métricas:
  - event_indexed vs validation_failed (ratio de calidad).
  - Tiempo promedio desde publish → index.
  - Crecimiento diario por dataset.
- Alertas:
  - Spike de `critical` > umbral.
  - Ausencia de eventos (silencio) por > N minutos.
  - Falla repetida de rollover.

## Seguridad
- Firma / hash del evento original (`event.original_hash`).
- Cifrado de campos sensibles (p.ej. PII) usando ingest processor personalizado.

## Multi-Tenant Escalado
- Alias por tenant: `logs-<tenant>`.
- Policy ISM por tenant (retenciones diferenciadas).
- Quotas (limitar volumen por período).

## Schema Registry Real
- Registrar evoluciones en SR (Confluent / Redpanda).
- Migrar consumer para validar esquema remoto (caching + fallback local).
- Estrategia de compatibilidad: BACKWARD, FORWARD, FULL.

## Optimización
- Ajustar número de shards (1 → evaluar tamaño > 50GB).
- Forzar segmentación por tipo de dataset si difieren cardinalidades (ej. logs-security-* vs logs-app-*).
- Comprimir (index.codec) en índices fríos.

## Reprocesamiento Histórico
- `_reindex` hacia nuevos índices optimizados.
- Aplicar pipeline extendido para añadir campos calculados (riesgo, score ML).