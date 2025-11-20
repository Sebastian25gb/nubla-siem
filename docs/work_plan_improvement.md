# Plan de Trabajo Integral – Nubla SIEM (Mejoras Técnicas y Operativas)

Este documento consolida las recomendaciones identificadas en la auditoría y las organiza en fases accionables con objetivos, entregables, criterios de aceptación y dependencias. El foco: robustecer ingest, multitenencia, seguridad, escalabilidad y calidad del código.

---

## 1. Principios Rectores

- Robustez primero: eliminar fuentes de error recurrentes (validación, DLQ, divergencias schema/mapping).
- Observabilidad exhaustiva: cada fase añade métricas y alertas asociadas.
- Multitenencia real antes de añadir nuevas fuentes o features avanzadas (reglas, NLP).
- Seguridad progresiva: hardening y autenticación integrados antes de escalar a entornos compartidos.
- Iteración con pruebas automatizadas (test-first para normalizador, consumer y assets operacionales).

---

## 2. Fases y Cronograma Referencial (sin fechas rígidas)

| Fase | Objetivo Macro | Duración estimada | Dependencias clave |
|------|----------------|-------------------|--------------------|
| 1    | Saneamiento Base & Testing | 1–2 semanas | Código actual estable |
| 2    | Bulk Ingest & Performance | 1–2 semanas | Fase 1 completada |
| 3    | Multitenencia Real | 2 semanas | Fase 1 y parte de 2 |
| 4    | Seguridad & Hardening | 2 semanas | Fase 3 (estructura índices) |
| 5    | Observabilidad Avanzada & Alertas | 1–2 semanas | Fases 1–4 |
| 6    | Reglas (Sigma) & Enriquecimiento | 2–3 semanas | Fases anteriores |
| 7    | ISM / Retención & Archivado | 1–2 semanas | Base estable ingest |
| 8    | Roadmap Futuro (NLP, SOAR-lite) | Continuo | Núcleo consolidado |

---

## 3. Detalle por Fase

### Fase 1 – Saneamiento Base & Testing
Objetivos:
- Unificar definición de schema (NCS) y mapping.
- Añadir suite de pruebas unitarias e integración.
- Documentar troubleshooting y estado actual vs visión.

Tareas:
1. Versionar schema como `backend/app/schema/ncs_v1.0.0.json`.
2. Crear carpeta `backend/tests/` con:
   - `test_normalizer_numeric_cast.py`
   - `test_consumer_validation.py` (mock de validator / index_event)
   - `test_index_event_fallback.py` (OpenSearch vs Elasticsearch)
3. Añadir script `scripts/diagnostics/check_mappings_vs_schema.py`.
4. Actualizar `README_OPERATIONS.md` con sección “Troubleshooting rápido”.
5. Definir convención casing severity: siempre lowercase (normalizador lo aplica, consumer ya no lo repite).
6. Pre-commit: black, isort, ruff.

Criterio de aceptación:
- `pytest` pasa al 100%.
- No divergencias reportadas por script de mappings/schema.
- README actualizado y visible.

### Fase 2 – Bulk Ingest & Performance
Objetivos:
- Incrementar throughput y reducir overhead por documento.
- Añadir métricas de latencia.

Tareas:
1. Implementar `bulk_indexer.py` (acumulación por tamaño o intervalo).
2. Ajustar `consumer.py` para:
   - Buffer interno (ej. lista de eventos hasta N=500 o flush cada 1s).
   - Prefetch dinámico (prefetch_count configurable vía ENV, p.ej. `CONSUMER_PREFETCH=25`).
3. Métricas nuevas: histogram `index_latency_seconds`, gauge `consumer_buffer_size`.
4. Evaluar compresión HTTP (`http_compress=True` en cliente).
5. Tabla comparativa antes/después (docs/benchmark/).

Criterio de aceptación:
- Throughput min. x5 comparado con ingest actual baseline.
- Latencia promedio y p95 visibles en /metrics.
- Sin aumento de DLQ.

### Fase 3 – Multitenencia Real
Objetivos:
- Aislamiento por índices y alias por tenant.
- Forzar presence de `tenant_id` y rechazo explícito si falta.
- Base para cuotas y RBAC futuro.

Tareas:
1. Normalizador: no autoasignar “default” si falta `tenant_id`; marcar error.
2. Crear estrategia indices: `logs-<tenant>-000001` + alias escritura `logs-<tenant>`.
3. Refactor template: remover patrón genérico “logs-*” para evitar contaminación cruzada.
4. Añadir script `scripts/tenancy/create_tenant_indices.sh`.
5. Métrica: contador por tenant (`events_indexed_total{tenant_id="x"}`).
6. Test integración: ingest dos tenants y query por cada alias sin fuga cruzada.
7. Documentar en `docs/architecture/multitenancy_design.md` la implementación actual.

Criterio de aceptación:
- Indices separados por tenant con alias correcto.
- Consumer rechaza eventos sin tenant_id (DLQ con razón `missing_tenant_id`).
- Tests confirman aislamiento.

### Fase 4 – Seguridad & Hardening
Objetivos:
- Autenticación en OpenSearch/Elasticsearch.
- Credenciales seguros RabbitMQ y política mínima de permisos.
- Base para TLS interno.

Tareas:
1. Habilitar OpenSearch Security Plugin (si no activo).
2. Crear roles: `tenant_reader`, `tenant_writer`, `ops_admin`.
3. Introducir variables OS_USER / OS_PASS en `.env` y usar en `elastic.py`.
4. Rotar credenciales RabbitMQ, remover `admin/securepass` de ejemplos productivos.
5. Documentar guía TLS (certs autogenerados + configuración docker).
6. Filtrar campos sensibles potenciales (whitelist vs blacklist en normalizador).
7. Añadir sección seguridad en README.

Criterio de aceptación:
- Autenticación activa; operaciones fallan sin credenciales.
- Roles aplicados; un usuario con rol lector no puede escribir.
- Documentación clara de pasos.

### Fase 5 – Observabilidad Avanzada & Alertas
Objetivos:
- Métricas extendidas (ratio fallos, lag, profundidad cola).
- Nuevas alertas operativas (validación, ingest backlog).

Tareas:
1. Exporter RabbitMQ queue depth (script polling → Prometheus).
2. Métricas: `validation_failure_ratio`, `dlq_depth`.
3. Monitores OpenSearch:
   - Ratio de `validation_failed` > umbral.
   - Bucket-level top `source.ip` crítico.
4. Throttling en alertas (evitar spam).
5. Dashboard base (Kibana/OpenSearch Dashboards) para ingest health.

Criterio de aceptación:
- Nuevas métricas accesibles y monitores activos.
- Dashboards con paneles: throughput, failure ratio, top sources.

### Fase 6 – Reglas (Sigma) & Enriquecimiento
Objetivos:
- Pipeline para traducción inicial Sigma → Query DSL.
- Enriquecimientos (Geo estándar ISO, reputación IP stub).

Tareas:
1. Carpeta `rules/sigma/` de ejemplo + traductor básico (subset).
2. Enriquecimiento modular: interfaz `enrichment_provider` + plugin dummy (geo dict).
3. Añadir campo `source.reputation.score` (placeholder).
4. Tests unidad sobre conversión mínima Sigma.
5. Documentar flujo reglas en `docs/architecture/rules_engine.md`.

Criterio de aceptación:
- 1–2 reglas Sigma transformadas y ejecutables manualmente.
- Enriquecimiento visible en documentos indexados.
- Tests de conversión pasan.

### Fase 7 – ISM / Retención & Archivado
Objetivos:
- Política de ciclo de vida consistente (hot/warm/cold/delete).
- Snapshot y restore básicos.

Tareas:
1. Consolidar todos los assets de ISM en `infra/opensearch/ism/`.
2. Definir política: hot 7d, warm 30d, cold 90d, delete 180d (ajustable).
3. Script `scripts/opensearch/install_ism.sh`.
4. Snapshot automático (cron contenedor) → `/usr/share/opensearch/snapshots`.
5. Documentar restore rápido.

Criterio de aceptación:
- `/_plugins/_ism/explain` refleja estado para índices nuevos.
- Snapshots generados y verificable restore en entorno aislado.

### Fase 8 – Roadmap Futuro (NLP, SOAR-lite)
Objetivos:
- Preparar base conceptual para siguientes pilares.
- Evitar bloqueo por falta de assets críticos previos.

Tareas (exploratorias):
1. Esqueleto conversión NL → DSL (no productivo).
2. Definir forma de playbooks (YAML) y motor de ejecución con aprobaciones.
3. ADRs para cada línea (NLP, SOAR).

Criterio de aceptación:
- ADRs en `docs/adrs/` con decisiones registradas.
- Protoboard de consultas NLP en sandbox.

---

## 4. Dependencias y Orden Estricto

1. Testing previo a optimizar (Fase 1).
2. Performance antes de multitenencia para dimensionar carga (Fase 2 → 3).
3. Seguridad después de estructura multi-tenant (Fase 4).
4. Observabilidad profunda una vez estable ingest (Fase 5).
5. Reglas y enriquecimiento requieren ingest y seguridad saneadas (Fase 6).
6. ISM y retención con datos ya segmentados (Fase 7).
7. Innovación (NLP / SOAR) tras la estabilidad básica (Fase 8).

---

## 5. Métricas a Implementar por Fase

| Métrica | Fase | Tipo | Descripción |
|---------|------|------|-------------|
| events_processed_total | Actual | Counter | Eventos consumidos |
| events_indexed_total | Actual | Counter | Eventos indexados |
| events_validation_failed_total | Actual | Counter | Fallos schema |
| consumer_buffer_size | 2 | Gauge | Eventos en buffer bulk |
| index_latency_seconds | 2 | Histogram | Latencia indexación |
| validation_failure_ratio | 5 | Gauge | (validation_failed / processed) |
| dlq_depth | 5 | Gauge | Mensajes pendientes DLQ |
| tenant_ingest_rate | 3 | Counter por label | Eventos/tenant |
| enrichment_latency_seconds | 6 | Histogram | Tiempo enriquecimiento |
| rollover_count | 7 | Counter | Rolled indices |
| snapshot_duration_seconds | 7 | Histogram | Tiempo snapshot |

---

## 6. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|-----------|
| Divergencia schema/mapping futura | Rechazos masivos | Script diff + test CI |
| Bulk ingestion mal calibrada | Pérdida de mensajes en crash | Flush por intervalo + graceful shutdown |
| Falta de seguridad prolongada | Exposición datos | Plan fase 4 acelerado, credenciales rotadas |
| Crecimiento DLQ silencioso | Pérdida valor operativo | Métrica dlq_depth + alerta |
| Multitenencia parcial (tenant_id default) | Fuga datos entre clientes | Validación estricta `tenant_id` obligatorio |
| Falta tests → regresiones | Inestabilidad | Test suite fase 1 bloqueo para merges |
| Exceso mappings dinámicos | Degradación búsqueda | Limitar dynamic templates y auditar campos |
| No rollover → índices gigantes | Penalización rendimiento | ISM fase 7 + alerta tamaño índice |

---

## 7. Artefactos Nuevos a Crear

| Archivo / Script | Ubicación | Propósito |
|------------------|-----------|----------|
| test_normalizer_numeric_cast.py | backend/tests/ | Validar casteo |
| test_consumer_validation.py | backend/tests/ | Flujos validación |
| bulk_indexer.py | backend/app/processing/ | Buffer + bulk |
| check_mappings_vs_schema.py | scripts/diagnostics/ | Auditoría |
| create_tenant_indices.sh | scripts/tenancy/ | Inicialización tenant |
| install_ism.sh | scripts/opensearch/ | ISM assets |
| rules_engine.md | docs/architecture/ | Diseño reglas |
| enrichment_provider.py | backend/app/enrichment/ | Interface plugin |
| replay_and_validate.py | scripts/dlq/ | Reprocesar DLQ con verificación |
| adr_*.md | docs/adrs/ | Registro decisiones futuras |

---

## 8. Criterios Globales de Calidad

- Cobertura mínima de tests iniciales: >= 70% en backend/app/processing y repository.
- Zero eventos permanentes en DLQ tras reprocesamiento regular (excepto quarantine intencional futura).
- Tiempo medio indexación < 200 ms (dev) y p95 < 500 ms en bulk.
- Validación: ratio fallos < 3% en flujo normal (alerta si > 10%).
- Documentación: cada artefacto operativo se acompaña de instrucciones idempotentes.

---

## 9. Checklist de Implementación por Fase (Resumen)

Fase 1:
- [ ] Schema versionado.
- [ ] Suite pytest inicial.
- [ ] Pre-commit hooks activos.
- [ ] README troubleshooting.

Fase 2:
- [ ] Bulk indexer integrado.
- [ ] Prefetch configurable.
- [ ] Métricas latencia.

Fase 3:
- [ ] Índices por tenant.
- [ ] Validación estricta tenant_id.
- [ ] Métricas por tenant.

Fase 4:
- [ ] Seguridad OpenSearch habilitada.
- [ ] Roles y credenciales rotados.
- [ ] TLS guía escrita.

Fase 5:
- [ ] Métricas avanzadas (ratio, dlq depth).
- [ ] Monitores nuevos.
- [ ] Dashboard ingest.

Fase 6:
- [ ] Enriquecimiento modular.
- [ ] Reglas Sigma prototipo.
- [ ] Tests conversión.

Fase 7:
- [ ] ISM política instalada.
- [ ] Rollover verificado.
- [ ] Snapshot + restore test.

Fase 8:
- [ ] ADRs NLP/SOAR.
- [ ] Protoboard NL→DSL.

---

## 10. Próxima Acción Inmediata

Iniciar Fase 1:
1. Crear carpeta `backend/tests`.
2. Añadir pruebas normalizador y consumer.
3. Versionar schema y corregir documentación severity.
4. Integrar ruff + black + isort (pyproject.toml).
5. Ejecutar primera pipeline CI (local) con `pytest`.

---

## 11. Notas Finales

Este plan es iterativo: cada fase debe concluir con revisión (code review + verificación métricas + actualización documentación) antes de avanzar. Ajustar duraciones según recursos disponibles.

---

## 12. Mantenimiento del Plan

- Actualizar este documento al finalizar cada fase (marcar checkboxes).
- Registrar cambios estructurales como ADR.
- Añadir enlace a tablero (Kanban) si se gestiona con issues en GitHub.

---

Fin del plan.