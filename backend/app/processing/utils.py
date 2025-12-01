from datetime import datetime, timezone
from typing import Any, Dict, List

from backend.app.core.config import settings


def to_iso8601(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return value


def coerce_datetimes(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: coerce_datetimes(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [coerce_datetimes(v) for v in obj]
    return to_iso8601(obj)


def prepare_event(evt: Dict[str, Any]) -> Dict[str, Any]:
    # Garantiza mínimos, normaliza datetimes y rellena tenant_id desde settings si falta
    if "@timestamp" not in evt:
        evt["@timestamp"] = evt.get("timestamp", datetime.now(timezone.utc).isoformat())
    evt = coerce_datetimes(evt)
    if "dataset" not in evt:
        evt["dataset"] = "syslog.generic"
    if "schema_version" not in evt:
        evt["schema_version"] = "1.0.0"
    # Relleno por defecto del tenant (útil en modos single-tenant o tests).
    # En modo estricto, el consumer puede validar previamente y rechazar antes de llamar a prepare_event.
    try:
        default_tenant = getattr(settings, "tenant_id", None)
    except Exception:
        default_tenant = None
    if "tenant_id" not in evt and default_tenant:
        evt["tenant_id"] = default_tenant
    return evt


def top_validation_errors(errors, limit: int = 5) -> List[str]:
    msgs: List[str] = []
    for e in list(errors)[:limit]:
        path = list(e.path) if getattr(e, "path", None) else []
        msgs.append(f"{getattr(e,'message','validation error')} (path: {path})")
    return msgs
