#!/usr/bin/env python3
"""
Onboarding de tenant:
- Añade tenant al registry (si no existe).
- Crea índice inicial logs-<tenant>-000001 y alias logs-<tenant> en OpenSearch.

Uso:
  python scripts/onboard_tenant.py <tenant_id>

Vars opcionales:
  TENANTS_REGISTRY_PATH (default: config/tenants.json)
  OPENSEARCH_HOST (default: opensearch:9200)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

TENANTS_PATH = Path(os.getenv("TENANTS_REGISTRY_PATH", "config/tenants.json"))
OS_HOST = os.getenv("OPENSEARCH_HOST", "opensearch:9200")


def load_tenants():
    if not TENANTS_PATH.exists():
        return []
    try:
        return json.loads(TENANTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_tenants(data):
    TENANTS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ensure_format(data):
    # Si es lista de strings, conviértela a objetos
    if not data:
        return []
    if isinstance(data[0], str):
        return [
            {"id": t, "status": "active", "valid_from": datetime.now(timezone.utc).isoformat()}
            for t in data
        ]
    return data


def create_index(tenant_id: str):
    base = f"http://{OS_HOST}"
    index = f"logs-{tenant_id}-000001"
    payload = {
        "aliases": {f"logs-{tenant_id}": {}},
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=f"{base}/{index}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 201):
                print(f"[WARN] OpenSearch index creation returned {resp.status}")
            else:
                print(f"[OK] Index + alias created: {index} -> logs-{tenant_id}")
    except error.HTTPError as e:
        print(
            f"[WARN] OpenSearch index creation failed ({e.code}): {e.read().decode('utf-8', 'ignore')}"
        )
    except Exception as e:
        print(f"[WARN] OpenSearch index creation error: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/onboard_tenant.py <tenant_id>")
        sys.exit(1)
    tenant_id = sys.argv[1].strip().lower().replace(" ", "-")
    if not tenant_id:
        print("Invalid tenant id")
        sys.exit(1)

    data = load_tenants()
    data = ensure_format(data)

    existing_ids = {d["id"] for d in data if isinstance(d, dict) and "id" in d}
    if tenant_id in existing_ids:
        print(f"[INFO] Tenant already present: {tenant_id}")
    else:
        data.append(
            {
                "id": tenant_id,
                "status": "active",
                "valid_from": datetime.now(timezone.utc).isoformat(),
            }
        )
        save_tenants(data)
        print(f"[OK] Tenant added to registry: {tenant_id}")

    create_index(tenant_id)


if __name__ == "__main__":
    main()
