#!/usr/bin/env python3
"""
Diagnóstico de divergencias entre el schema NCS local y el mapping de un índice OpenSearch.

Uso:
  python scripts/diagnostics/check_mappings_vs_schema.py --index logs-default --host http://localhost:9201

Salida (JSON):
{
  "index": "logs-default",
  "missing_in_mapping": [...],
  "extra_in_mapping": [...],
  "type_mismatches": [...],
  "schema_fields": N,
  "mapping_fields": M,
  "ok": bool
}

Notas:
- Comparación superficial: presencia de campo y coincidencia de tipo.
- Ajusta extract_schema_fields si el schema evoluciona.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import requests


def load_schema(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        print(json.dumps({"error": "schema_not_found", "path": path}))
        sys.exit(1)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def fetch_mapping(host: str, index: str) -> Dict[str, Any]:
    url = f"{host.rstrip('/')}/{index}/_mapping"
    r = requests.get(url, timeout=10)
    if r.status_code >= 300:
        print(json.dumps({"error": "mapping_request_failed", "status": r.status_code, "url": url}))
        sys.exit(2)
    return r.json()


def flatten_mapping(mapping: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}

    def _walk(props: Dict[str, Any], prefix: str = ""):
        for k, v in props.items():
            path = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
            vtype = v.get("type")
            subprops = v.get("properties")
            if vtype:
                out[path] = vtype
            if subprops and isinstance(subprops, dict):
                _walk(subprops, path)

    if not mapping:
        return out
    first = next(iter(mapping.values()))
    props = first.get("mappings", {}).get("properties", {})
    if isinstance(props, dict):
        _walk(props, "")
    return out


def extract_schema_fields(schema: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}

    def _walk(props: Dict[str, Any], prefix: str = ""):
        for k, v in props.items():
            path = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
            vtype = v.get("type")
            subprops = v.get("properties")
            if vtype:
                out[path] = vtype
            if subprops and isinstance(subprops, dict):
                _walk(subprops, path)

    root_props = schema.get("properties", {})
    if isinstance(root_props, dict):
        _walk(root_props, "")
    return out


def compute_diff(schema_fields: Dict[str, str], mapping_fields: Dict[str, str]) -> Dict[str, Any]:
    schema_keys: Set[str] = set(schema_fields.keys())
    mapping_keys: Set[str] = set(mapping_fields.keys())

    missing = sorted(schema_keys - mapping_keys)
    extra = sorted(mapping_keys - schema_keys)

    type_mismatches: List[Dict[str, str]] = []
    for k in sorted(schema_keys & mapping_keys):
        st = schema_fields.get(k)
        mt = mapping_fields.get(k)
        if st and mt and st != mt:
            type_mismatches.append({"field": k, "schema_type": st, "mapping_type": mt})

    return {
        "missing_in_mapping": missing,
        "extra_in_mapping": extra,
        "type_mismatches": type_mismatches,
        "schema_fields": len(schema_fields),
        "mapping_fields": len(mapping_fields),
        "ok": not missing and not type_mismatches,
    }


def main():
    parser = argparse.ArgumentParser(description="Diff schema NCS vs mapping de índice OpenSearch.")
    parser.add_argument("--schema", default="backend/app/schema/ncs_v1.0.0.json")
    parser.add_argument("--host", default="http://localhost:9201")
    parser.add_argument("--index", default="logs-default")
    args = parser.parse_args()

    schema = load_schema(args.schema)
    mapping = fetch_mapping(args.host, args.index)

    schema_fields = extract_schema_fields(schema)
    mapping_fields = flatten_mapping(mapping)

    diff = compute_diff(schema_fields, mapping_fields)
    diff.update({"index": args.index})
    print(json.dumps(diff, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
