import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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
    # Garantiza mínimos, normaliza datetimes
    if "@timestamp" not in evt:
        evt["@timestamp"] = evt.get("timestamp", datetime.now(timezone.utc).isoformat())
    evt = coerce_datetimes(evt)
    evt.setdefault("dataset", "syslog.generic")
    evt.setdefault("schema_version", "1.0.0")
    return evt

def top_validation_errors(errors, limit: int = 5) -> List[str]:
    msgs: List[str] = []
    for e in list(errors)[:limit]:
        path = list(e.path) if getattr(e, "path", None) else []
        msgs.append(f"{getattr(e,'message','validation error')} (path: {path})")
    return msgs