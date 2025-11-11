# Rollover e Index State Management (ISM)

## Alias y Write Index
Alias: `logs-default`
Write index: índice que tiene `"is_write_index": true`.

## Ciclo Rollover Manual
1. Condiciones se cumplen (`max_docs`, `max_size`).
2. POST /logs-default/_rollover crea logs-default-00000(N+1).
3. Alias `logs-default` pasa a apuntar al nuevo índice como write.

## ISM Policy (logs-default-ism)
Estados:
- hot: acción rollover (min_index_age 1d, min_size 1gb, min_doc_count 100000).
- delete: elimina índice tras 7d.

Requisito de cada índice gestionado:
```json
"index.opendistro.index_state_management.rollover_alias": "logs-default"
```

## Ver Estado
```bash
curl -sS 'http://localhost:9201/_plugins/_ism/explain/logs-default-00000X' | jq
```

Campos relevantes:
| Campo | Significado |
|-------|-------------|
| state.name | Estado actual (hot/delete) |
| action.name | Acción en progreso (rollover/delete) |
| step.name | Paso interno (attempt_rollover) |
| info.message | Mensaje de diagnóstico |

## Errores Comunes
| Mensaje | Causa | Solución |
|---------|-------|----------|
| Missing rollover_alias | Falta setting en índice | PUT _settings agregando la key |
| This index has no metadata information | Adjuntar policy con ADD y esperar ejecución | Reintentar tras fijar alias |
| step_status = failed | Condición insatisfecha o config incompleta | Revisar info.message |

## Ajustar Condiciones de Rollover
Editar policy (PUT):
- `min_index_age`
- `min_size`
- `min_doc_count`

## Delete State
Cuando `min_index_age: 7d` del índice se cumple en hot → transición a delete → acción `delete`.
