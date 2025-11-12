#!/usr/bin/env python3
"""
Normalizador Fortinet mejorado.

- Elimina prefijo syslog "<PRI>" si existe.
- Extrae key=value (soporta quoted values).
- Soporta eventtime (epoch en ns) -> @timestamp ISO.
- Extrae devname/devid -> host, host_name.
- Extrae msg -> message (si existe) y srcip/dstip -> source/destination.ip.
- Guarda copia original en original.message_raw y original.raw_kv.
"""
import re
from datetime import datetime, timezone
from typing import Any, Dict

KV_RE = re.compile(r'(\w+)=(".*?"|[^"\s]+)')
PRI_RE = re.compile(r'^<\d+>')

def parse_kv(s: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for m in KV_RE.finditer(s):
        k = m.group(1)
        v = m.group(2)
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        out[k] = v
    return out

def ns_epoch_to_iso(ns_str: str) -> str:
    try:
        ns = int(ns_str)
        ms = ns // 1_000_000
        dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        return dt.isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()

def strip_pri(s: str) -> str:
    return PRI_RE.sub('', s, count=1)

def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    # Passthrough si no es dict o no contiene "message"
    if not isinstance(raw, dict):
        return raw
    msg_raw = raw.get("message")
    if not isinstance(msg_raw, str):
        return raw

    out: Dict[str, Any] = {}
    out["original"] = out.get("original", {})
    out["original"]["message_raw"] = msg_raw

    cleaned = strip_pri(msg_raw).strip()
    kv = parse_kv(cleaned)
    out["original"]["raw_kv"] = kv

    out["tenant_id"] = raw.get("tenant_id", "default")
    out["dataset"] = raw.get("dataset", "syslog.generic")
    out["schema_version"] = raw.get("schema_version", "1.0.0")

    # timestamp
    ts = None
    if "eventtime" in kv:
        ts = ns_epoch_to_iso(kv.get("eventtime"))
    else:
        date = kv.get("date")
        timev = kv.get("time")
        tz = kv.get("tz")
        if date and timev:
            try:
                if tz and re.match(r'^[+-]\d{4}$', tz):
                    tz = tz[:3] + ":" + tz[3:]
                if tz:
                    ts = f"{date}T{timev}{tz}"
                else:
                    ts = f"{date}T{timev}Z"
            except Exception:
                ts = None
    if ts is None:
        ts = raw.get("@timestamp") or raw.get("timestamp") or datetime.now(timezone.utc).isoformat()
    out["@timestamp"] = ts

    # message text
    if "msg" in kv:
        out["message"] = kv.get("msg")
    else:
        out["message"] = cleaned

    # severity
    severity = raw.get("severity")
    if not severity:
        severity = kv.get("severity") or kv.get("level") or kv.get("crlevel")
    out["severity"] = str(severity).lower() if severity else "info"

    # host detection
    host = raw.get("host") or kv.get("devname") or kv.get("devid")
    if host:
        out["host"] = host
        out["host_name"] = host

    # network addresses
    if "srcip" in kv:
        out.setdefault("source", {})["ip"] = kv.get("srcip")
    if "dstip" in kv:
        out.setdefault("destination", {})["ip"] = kv.get("dstip")

    # useful labels
    labels = {}
    for k in ("attack","policyid","service","proto"):
        if k in kv:
            labels[k] = kv.get(k)
    if labels:
        out["labels"] = labels

    return out