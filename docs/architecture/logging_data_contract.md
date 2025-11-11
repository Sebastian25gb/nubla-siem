# Data Contract de Eventos de Log

## Ejemplo de Evento Válido

```json
{
  "tenant_id": "default",
  "@timestamp": "2025-11-11T15:34:22.135326Z",
  "severity": "info",
  "dataset": "syslog.generic",
  "schema_version": "1.0.0",
  "message": "valid event",
  "source": {
    "ip": "127.0.0.1"
  }
}
```

## Campos Requeridos (Schema)
| Campo | Tipo | Requerido | Ejemplo | Notas |
|-------|------|-----------|---------|-------|
| tenant_id | string | Sí | default | Segmentación |
| @timestamp | string (ISO8601) | Sí | 2025-11-11T15:34:22Z | Normalizado |
| severity | enum | Sí | info | low, medium, high, critical, info |
| dataset | string | Sí | syslog.generic | Clasificación |
| schema_version | string | Sí | 1.0.0 | Evolución controlada |
| message | string | Sí | valid event | Texto base |

## Campos Opcionales
| Campo | Tipo | Ejemplo |
|-------|------|---------|
| source.ip | ip | 127.0.0.1 |
| host | string | server-01 |
| facility | string | auth |

## Reglas de Validación
- `@timestamp` como ISO (consumer convierte datetimes).
- `severity` debe ser uno de los valores enumerados.
- Si faltan `dataset` o `schema_version`, consumer los completa con default.

## Evolución del Schema
1. Introducir campo nuevo → marcarlo opcional inicialmente.
2. Actualizar schema local → subir commit.
3. (Futuro) Registrar en Schema Registry central.
4. Hacerlo requerido tras validar adopción (fase de transición).

## Manejo de Versiones (`schema_version`)
- Cambios compatibles menores → incrementar patch (1.0.x).
- Nuevos campos opcionales → minor (1.x.0).
- Cambios incompatibles / campos requeridos nuevos → major (2.0.0).
