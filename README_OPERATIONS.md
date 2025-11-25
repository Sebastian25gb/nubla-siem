# Operaciones: Rollover e ISM

Este repositorio indexa eventos en índices por tenant usando alias `logs-<tenant>` y nombre físico `logs-<tenant>-000001`, `logs-<tenant>-000002`, etc.

## 1. Rollover Manual (Script existente)

Script: `scripts/rollover_tenant_index.py`

Comandos claves:
```bash
# Ver estado
python scripts/rollover_tenant_index.py --tenant delawarehotel --check

# Rollover forzado por doc count (si índice ya tiene ≥1 doc)
python scripts/rollover_tenant_index.py --tenant delawarehotel --rollover --max-docs 1
```

Respuesta típica de rollover:
```json
{
  "acknowledged": true,
  "old_index": "logs-delawarehotel-000001",
  "new_index": "logs-delawarehotel-000002",
  "rolled_over": true,
  "conditions": {
    "[max_docs: 1]": true
  }
}
```

## 2. Index State Management (ISM) Automático

Para evitar cron y scripts manuales, OpenSearch ISM permite definir políticas que:
- Hacen rollover según condiciones (edad, tamaño, número de documentos).
- Eliminar índices tras periodo de retención.

### Script: `scripts/apply_ism_policy.py`

Genera y aplica por tenant:
- Política `logs-<tenant>-policy`
- Index template `logs-<tenant>-template` con alias de rollover y la política.

Ejemplo (tenant delawarehotel):
```bash
export OPENSEARCH_HOST=http://localhost:9201
export OS_USER=admin
export OS_PASS=admin

python scripts/apply_ism_policy.py --tenant delawarehotel \
  --min-index-age-rollover 1d \
  --min-size-rollover 50gb \
  --min-docs-rollover 10000000 \
  --delete-after-age 30d \
  --shards 1 \
  --replicas 0
```

Dry-run (no persiste):
```bash
python scripts/apply_ism_policy.py --tenant delawarehotel --dry-run
```

Adjuntar política a índices ya existentes:
```bash
python scripts/apply_ism_policy.py --tenant delawarehotel --attach-existing
```

### Verificación

1. Listar política:
```bash
curl -s $OPENSEARCH_HOST/_plugins/_ism/policies/logs-delawarehotel-policy | jq .
```

2. Ver template:
```bash
curl -s $OPENSEARCH_HOST/_index_template/logs-delawarehotel-template | jq .
```

3. Ver settings índice actual:
```bash
curl -s $OPENSEARCH_HOST/logs-delawarehotel-000001/_settings | jq '.[] | .settings | {policy_id: ."opendistro.index_state_management.policy_id", rollover_alias: ."index.lifecycle.rollover_alias"}'
```

### Cómo ocurre el rollover automático

Cuando el índice write (`is_write_index=true`) cumple las condiciones:
- Edad ≥ `min_index_age`
- Tamaño ≥ `min_size`
- Documentos ≥ `min_doc_count`

El plugin crea `logs-<tenant>-00000N+1`, mueve el alias de escritura y el índice anterior queda “sellado”.

### Estado y Depuración

Ver estado ISM de un índice:
```bash
curl -s $OPENSEARCH_HOST/_plugins/_ism/explain/logs-delawarehotel-000001 | jq .
```

Respuesta típica:
```json
{
  "logs-delawarehotel-000001": {
    "index.plugins.index_state_management.policy_id": "logs-delawarehotel-policy",
    "index_state_management": {
      "name": "hot",
      "start_time": 1700000000000,
      "managed": true,
      "policy_id": "logs-delawarehotel-policy"
    }
  }
}
```

### Eliminación automática

Índices cumplirán transición a estado `delete` cuando la edad supere `delete_after_age`. El estado `delete` ejecuta acción `delete`.

### Cambiar parámetros de la política

Actualizar política (reaplicar con nuevos valores):
```bash
python scripts/apply_ism_policy.py --tenant delawarehotel --min-index-age-rollover 12h --min-size-rollover 10gb --min-docs-rollover 2000000 --delete-after-age 14d
```

### Precauciones

- Reducir demasiado las condiciones puede crear muchos índices (impacto en administración).
- Asegurar que el alias `logs-<tenant>` existe antes si migras desde un entorno manual.
- En entornos con multi-tenant masivo, evaluar separar políticas por clase de tenant (gold/silver/bronze) para evitar docenas de políticas independientes.

## 3. Ejemplo de Política Genérica

Archivo: `policies/ism_logs_generic.json` (base para copiar).
Cambiar `index_patterns` o aplicar por script para tenants específicos.

## 4. Limpieza Manual (Si no se usa ISM delete)

Para eliminar índices antiguos sin política:
```bash
curl -XDELETE $OPENSEARCH_HOST/logs-delawarehotel-000001
```
Asegúrate que NO sea el índice write actual (`is_write_index=true`).

## 5. Integración con Métricas

Agregar un exporter o job que recoja:
```bash
/_cat/indices/logs-<tenant>-*?bytes=gb&h=index,docsCount,storeSize
```
y convierta a métricas Prometheus (custom script) para ver crecimiento y disparadores futuros.

## 6. Próximos Pasos Recomendados

- Añadir script `scripts/explain_ism.py` para listar estado de todos los índices.
- Panel Grafana: docsCount vs tiempo + número de índices por tenant.
- Consolidar rotación de alias en un health-check diario (verifica que write_index está marcado).

### Alias y Rollover (Centralización)

Pasos para mantener un alias con un único write index:

1. Ver alias:
   ```bash
   curl -s -u admin:admin "$OPENSEARCH_HOST/_alias/logs-default" | jq .
   ```

2. Normalizar (si más de un write):
   ```bash
   cat > fix_alias.json <<'EOF'
   {
     "actions": [
       {"remove": {"index": "logs-default-000001", "alias": "logs-default"}},
       {"add": {"index": "logs-default-000001", "alias": "logs-default", "is_write_index": false}},
       {"remove": {"index": "logs-default-000002", "alias": "logs-default"}},
       {"add": {"index": "logs-default-000002", "alias": "logs-default", "is_write_index": true}}
     ]
   }
   EOF
   curl -XPOST -u admin:admin "$OPENSEARCH_HOST/_aliases" -d @fix_alias.json
   ```

3. Evento de prueba:
   ```bash
   curl -XPOST -u admin:admin "$OPENSEARCH_HOST/logs-default/_doc?pipeline=logs_ingest" \
     -H 'Content-Type: application/json' \
     -d '{"@timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","tenant_id":"default","severity":"info","message":"test"}'
   ```

4. Ver count:
   ```bash
   curl -s -u admin:admin "$OPENSEARCH_HOST/logs-default-000002/_count"
   ```

### Snapshot previo a delete
Ver sección scripts/snapshot_before_delete.py y programar cron diario.