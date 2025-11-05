import re
import shlex
from datetime import datetime
from typing import Optional

from domain.schemas import LogEvent

PRI_PREFIX = re.compile(r"^<\d+>\s*")

def _parse_kv_message(msg: str) -> dict:
    """
    Parsea mensajes Fortinet estilo key=value con comillas.
    Ej: date=2025-11-03 time=19:15:32 devname="X" severity="critical" ...
    """
    # Quita prefijo PRI de syslog si viene (<185>)
    msg = PRI_PREFIX.sub("", msg)
    # Divide respetando comillas
    parts = shlex.split(msg)
    kv = {}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            kv[k] = v
    return kv

def _parse_timestamp(kv: dict) -> Optional[datetime]:
    # Intenta construir timestamp con date + time + tz (si existe)
    try:
        date = kv.get("date")
        time_ = kv.get("time")
        tz = kv.get("tz", "+0000").strip('"')
        if date and time_:
            # tz esperado como +HHMM o -HHMM; si no existe, se usa +0000
            return datetime.strptime(f"{date} {time_} {tz}", "%Y-%m-%d %H:%M:%S %z")
    except Exception:
        pass
    # Fortinet también envía eventtime con epoch en ns/us; lo omitimos por ahora
    return None

def normalize(raw: dict) -> LogEvent:
    """
    - Si 'message' contiene Fortinet key=value, se parsea y se intentan mapear campos.
    - En otros casos, se conserva el message original.
    """
    message = raw.get("message") or raw.get("msg") or ""
    host = raw.get("host") or raw.get("hostname")
    facility = raw.get("facility")
    severity = raw.get("severity")
    tenant_id = raw.get("tenant_id") or "default"

    # Intento de parse Fortinet
    kv = {}
    if "=" in message:
        kv = _parse_kv_message(message)
        # Mapear algunos campos comunes
        host = host or kv.get("devname")
        severity = severity or kv.get("severity")
        # Si Fortinet lleva un msg=... propio, prefierelo
        message = kv.get("msg") or kv.get("message") or message

    ts = _parse_timestamp(kv) if kv else None

    if ts:
        return LogEvent(timestamp=ts, message=message, host=host, facility=facility, severity=severity, tenant_id=tenant_id)
    else:
        return LogEvent(message=message, host=host, facility=facility, severity=severity, tenant_id=tenant_id)