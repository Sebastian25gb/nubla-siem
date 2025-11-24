#!/usr/bin/env python
from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import requests


def _normalize_url(raw: Optional[str]) -> str:
    raw = (raw or "").strip()
    if not raw:
        return "http://localhost:9201"
    if raw.startswith(("http://", "https://")):
        return raw
    if ":" in raw:
        return f"http://{raw}"
    return f"http://{raw}:9200"


def http_client():
    base = _normalize_url(os.getenv("OPENSEARCH_HOST"))
    user = os.getenv("OS_USER") or os.getenv("ES_USER")
    pwd = os.getenv("OS_PASS") or os.getenv("ES_PASS")
    auth = (user, pwd) if user and pwd else None
    s = requests.Session()
    s.headers["Content-Type"] = "application/json"
    s.base_url = base  # type: ignore
    s.auth = auth
    return s


def build_policy(tenant: str, age: str, size: str, docs: int, delete_age: str) -> Dict[str, Any]:
    return {
        "policy": {
            "policy_id": f"logs-{tenant}-policy",
            "description": f"Rollover y borrado automático para tenant {tenant}",
            "schema_version": 1,
            "default_state": "hot",
            "states": [
                {
                    "name": "hot",
                    "actions": [
                        {
                            "rollover": {
                                "min_index_age": age,
                                "min_size": size,
                                "min_doc_count": docs,
                            },
                            "retry": {"count": 3, "backoff": "exponential", "delay": "1m"},
                        }
                    ],
                    "transitions": [
                        {"state_name": "delete", "conditions": {"min_index_age": delete_age}}
                    ],
                },
                {
                    "name": "delete",
                    "actions": [
                        {
                            "delete": {},
                            "retry": {"count": 3, "backoff": "exponential", "delay": "1m"},
                        }
                    ],
                    "transitions": [],
                },
            ],
            "ism_template": [{"index_patterns": [f"logs-{tenant}-*"], "priority": 100}],
        }
    }


def build_template(tenant: str, shards: int, replicas: int) -> Dict[str, Any]:
    return {
        "index_patterns": [f"logs-{tenant}-*"],
        "priority": 100,
        "template": {
            "settings": {"number_of_shards": shards, "number_of_replicas": replicas},
            "aliases": {f"logs-{tenant}": {}},
        },
        "_meta": {"tenant": tenant, "created": datetime.datetime.utcnow().isoformat() + "Z"},
    }


def list_indices(session, tenant: str) -> List[str]:
    pattern = f"logs-{tenant}-*"
    resp = session.get(f"{session.base_url}/{pattern}")
    if resp.status_code == 404:
        return []
    data = resp.json()
    return sorted(data.keys())


def put_policy(session, body: Dict[str, Any], dry_run: bool, force: bool) -> Dict[str, Any]:
    pid = body["policy"]["policy_id"]
    url = f"{session.base_url}/_plugins/_ism/policies/{pid}"
    if force and not dry_run:
        session.delete(url)
    if dry_run:
        return {"dry_run": True, "request": body}
    resp = session.put(url, data=json.dumps(body))
    if resp.status_code not in (200, 201):
        # Ignora 409 si ya existe
        if resp.status_code == 409:
            return {"status": 409, "exists": True}
        raise RuntimeError(f"Error policy {pid}: {resp.status_code} {resp.text}")
    return {"status": resp.status_code, "body": resp.json()}


def put_template(session, tenant: str, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    name = f"logs-{tenant}-template"
    url = f"{session.base_url}/_index_template/{name}"
    if dry_run:
        return {"dry_run": True, "request": body}
    resp = session.put(url, data=json.dumps(body))
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Error template {name}: {resp.status_code} {resp.text}")
    return {"status": resp.status_code, "body": resp.json()}


def attach_policy(session, index: str, policy_id: str, dry_run: bool) -> Dict[str, Any]:
    url = f"{session.base_url}/_plugins/_ism/add/{index}"
    payload = {"policy_id": policy_id}
    if dry_run:
        return {"index": index, "dry_run": True, "request": payload}
    resp = session.post(url, data=json.dumps(payload))
    return {"index": index, "status": resp.status_code, "body": safe_json(resp)}


def set_rollover_alias(session, index: str, alias: str, dry_run: bool) -> Dict[str, Any]:
    url = f"{session.base_url}/{index}/_settings"
    payload = {"index.opendistro.index_state_management.rollover_alias": alias}
    if dry_run:
        return {"index": index, "dry_run": True, "request": payload}
    resp = session.put(url, data=json.dumps({"settings": payload}))
    return {"index": index, "status": resp.status_code, "body": safe_json(resp)}


def safe_json(resp) -> Any:
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--tenant", required=True)
    p.add_argument("--min-index-age-rollover", default="1d")
    p.add_argument("--min-size-rollover", default="50gb")
    p.add_argument("--min-docs-rollover", type=int, default=10_000_000)
    p.add_argument("--delete-after-age", default="30d")
    p.add_argument("--shards", type=int, default=1)
    p.add_argument("--replicas", type=int, default=0)
    p.add_argument("--attach-existing", action="store_true")
    p.add_argument(
        "--set-rollover-alias",
        action="store_true",
        help="Aplica rollover_alias al último índice (escritura)",
    )
    p.add_argument("--force-update-policy", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(message)s"
    )
    session = http_client()

    # Check plugin
    ping = session.get(f"{session.base_url}/_plugins/_ism/policies")
    if ping.status_code not in (200, 404):
        print(
            json.dumps(
                {
                    "error": "ISM plugin no accesible",
                    "status": ping.status_code,
                    "body": safe_json(ping),
                },
                indent=2,
            )
        )
        sys.exit(1)

    policy_body = build_policy(
        args.tenant,
        args.min_index_age_rollover,
        args.min_size_rollover,
        args.min_docs_rollover,
        args.delete_after_age,
    )
    policy_id = policy_body["policy"]["policy_id"]
    policy_result = put_policy(session, policy_body, args.dry_run, args.force_update_policy)

    template_body = build_template(args.tenant, args.shards, args.replicas)
    template_result = put_template(session, args.tenant, template_body, args.dry_run)

    attach_result = None
    alias_result = None
    if args.attach_existing or args.set_rollover_alias:
        indices = list_indices(session, args.tenant)
        if args.attach_existing:
            details = []
            for idx in indices:
                details.append(attach_policy(session, idx, policy_id, args.dry_run))
            attach_result = {"count": len(details), "details": details}
        if args.set_rollover_alias and indices:
            write_index = indices[-1]
            alias_result = set_rollover_alias(
                session, write_index, f"logs-{args.tenant}", args.dry_run
            )

    output = {
        "policy_result": policy_result,
        "template_result": template_result,
        "attach_existing": attach_result,
        "rollover_alias_set": alias_result,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
