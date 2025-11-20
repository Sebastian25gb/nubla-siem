#!/usr/bin/env python3
"""
Normalizador Fortinet extendido.
Castea campos numéricos (puertos, count, crscore, pps) a int para cumplir con el schema.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

KV_RE = re.compile(r'(\w+)=(".*?"|[^"\s]+)')
PRI_RE = re.compile(r'^<\d+>')
PPS_RE = re.compile(r'pps\s+(\d+)\b')

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

def to_int_safe(v: Optional[str]) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(v)
    except Exception:
        return None

def strip_pri(s: str) -> str:
    return PRI_RE.sub('', s, count=1)

def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
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
                ts = f"{date}T{timev}{tz}" if tz else f"{date}T{timev}Z"
            except Exception:
                ts = None
    if ts is None:
        ts = raw.get("@timestamp") or raw.get("timestamp") or datetime.now(timezone.utc).isoformat()
    out["@timestamp"] = ts

    out["message"] = kv.get("msg") or cleaned

    sev_in = raw.get("severity") or kv.get("severity") or kv.get("level") or kv.get("crlevel") or "info"
    out["severity_original"] = str(sev_in)
    out["severity"] = sev_in

    host = raw.get("host") or kv.get("devname") or kv.get("devid")
    if host:
        out["host"] = host
        out["host_name"] = host

    if "srcip" in kv:
        out.setdefault("source", {})["ip"] = kv.get("srcip")
    if "dstip" in kv:
        out.setdefault("destination", {})["ip"] = kv.get("dstip")

    sp = to_int_safe(kv.get("srcport"))
    if sp is not None:
        out.setdefault("source", {})["port"] = sp
    dp = to_int_safe(kv.get("dstport"))
    if dp is not None:
        out.setdefault("destination", {})["port"] = dp

    if "proto" in kv:
        out.setdefault("network", {})["protocol"] = kv.get("proto")

    if "attack" in kv:
        out.setdefault("threat", {})["name"] = kv.get("attack")
    if "attackid" in kv:
        out.setdefault("threat", {})["id"] = kv.get("attackid")
    crscore = to_int_safe(kv.get("crscore"))
    if crscore is not None:
        out.setdefault("threat", {})["score"] = crscore
    if "craction" in kv:
        out.setdefault("threat", {})["action"] = kv.get("craction")

    if "policyid" in kv:
        out.setdefault("rule", {})["id"] = kv.get("policyid")

    cnt = to_int_safe(kv.get("count"))
    if cnt is not None:
        out.setdefault("event", {})["count"] = cnt

    pps_match = PPS_RE.search(cleaned)
    if pps_match:
        pps_val = to_int_safe(pps_match.group(1))
        if pps_val is not None:
            out.setdefault("flow", {})["packets_per_second"] = pps_val

    if "srccountry" in kv:
        out.setdefault("source", {}).setdefault("geo", {})["country_iso_code"] = kv.get("srccountry").strip().upper().replace(" ", "_")
    if "dstcountry" in kv:
        out.setdefault("destination", {}).setdefault("geo", {})["country_iso_code"] = kv.get("dstcountry").strip().upper().replace(" ", "_")

    labels = {}
    for k in ("service", "proto"):
        if k in kv:
            labels[k] = kv.get(k)
    if labels:
        out["labels"] = labels

    return out