#!/usr/bin/env python
"""
Aplicación de políticas ISM (Index State Management) por tenant en OpenSearch.

Flujo:
1. Crea (o actualiza) la política logs-<tenant>-policy con estados hot y delete.
2. Crea (o actualiza) un index template composable logs-<tenant>-template con patrón logs-<tenant>-*.
3. Opcionalmente adjunta la política a índices existentes usando el endpoint /_plugins/_ism/add/<index>.
4. Permite dry-run para ver payloads sin persistir.
"""
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
    fallback = "http://localhost:9201"
    raw = (raw or "").strip()
    if not raw:
        return fallback
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
    session = requests.Session()
    session.headers["Content-Type"] = "application/json"
    session.base_url = base  # type: ignore
    session.auth = auth
    return session


def build_policy(
    tenant: str,
    min_index_age_rollover: str,
    min_size_rollover: str,
    min_docs_rollover: int,
    delete_after_age: str,
) -> Dict[str, Any]:
    policy_id = f"logs-{tenant}-policy"
    return {
        "policy": {
            "policy_id": policy_id,
            "description": f"Rollover y borrado automático para tenant {tenant}",
            "schema_version": 1,
            "error_notification": None,
            "default_state": "hot",
            "states": [
                {
                    "name": "hot",
                    "actions": [
                        {
                            "rollover": {
                                "min_index_age": min_index_age_rollover,
                                "min_size": min_size_rollover,
                                "min_doc_count": min_docs_rollover,
                            },
                            "retry": {
                                "count": 3,
                                "backoff": "exponential",
                                "delay": "1m",
                            },
                        }
                    ],
                    "transitions": [
                        {
                            "state_name": "delete",
                            "conditions": {
                                "min_index_age": delete_after_age,
                            },
                        }
                    ],
                },
                {
                    "name": "delete",
                    "actions": [
                        {
                            "delete": {},
                            "retry": {
                                "count": 3,
                                "backoff": "exponential",
                                "delay": "1m",
                            },
                        }
                    ],
                    "transitions": [],
                },
            ],
            "ism_template": [
                {
                    "index_patterns": [f"logs-{tenant}-*"],
                    "priority": 100,
                }
            ],
        }
    }


def build_index_template(
    tenant: str,
    shards: int,
    replicas: int,
    policy_id: str,
) -> Dict[str, Any]:
    """
    Composable index template (sin wrapper 'index_template' en body).
    """
    return {
        "index_patterns": [f"logs-{tenant}-*"],
        "template": {
            "settings": {
                "number_of_shards": shards,
                "number_of_replicas": replicas,
                # Varias claves para distintas versiones/compatibilidad.
                "opendistro.index_state_management.policy_id": policy_id,
                "index.opendistro.index_state_management.policy_id": policy_id,
                "opensearch.index_state_management.policy_id": policy_id,
                "index.lifecycle.rollover_alias": f"logs-{tenant}",
            },
            "aliases": {f"logs-{tenant}": {}},
        },
        "priority": 100,
        "_meta": {
            "tenant": tenant,
            "description": "Template de logs con rollover automático via ISM",
            "created": datetime.datetime.utcnow().isoformat() + "Z",
        },
    }


def safe_json(resp) -> Any:
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


def put_policy(session, policy_json: Dict[str, Any], dry_run: bool, force: bool) -> Dict[str, Any]:
    policy_id = policy_json["policy"]["policy_id"]
    url = f"{session.base_url}/_plugins/_ism/policies/{policy_id}"
    if force and not dry_run:
        # Borrar primero (ignorar si no existe)
        del_resp = session.delete(url)
        logging.info("policy_delete_attempt", extra={"status": del_resp.status_code})
    resp = session.put(url, data=json.dumps(policy_json))
    if dry_run:
        return {
            "dry_run": True,
            "request": policy_json,
            "status_code": resp.status_code,
            "body": safe_json(resp),
        }
    if resp.status_code == 409:
        logging.warning("policy_exists_version_conflict_ignored", extra={"policy_id": policy_id})
        return {"status_code": resp.status_code, "body": safe_json(resp), "ignored_conflict": True}
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Error creando/actualizando política {policy_id}: {resp.status_code} {resp.text}"
        )
    return {"status_code": resp.status_code, "body": safe_json(resp)}


def put_index_template(
    session, tenant: str, template_json: Dict[str, Any], dry_run: bool
) -> Dict[str, Any]:
    name = f"logs-{tenant}-template"
    url = f"{session.base_url}/_index_template/{name}"
    resp = session.put(url, data=json.dumps(template_json))
    if dry_run:
        return {
            "dry_run": True,
            "request": template_json,
            "status_code": resp.status_code,
            "body": safe_json(resp),
        }
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Error creando/actualizando index template {name}: {resp.status_code} {resp.text}"
        )
    return {"status_code": resp.status_code, "body": safe_json(resp)}


def list_existing_indices(session, tenant: str) -> List[str]:
    pattern = f"logs-{tenant}-*"
    url = f"{session.base_url}/{pattern}"
    resp = session.get(url)
    if resp.status_code == 404:
        return []
    data = safe_json(resp)
    return list(data.keys())


def attach_policy(session, index: str, policy_id: str, dry_run: bool) -> Dict[str, Any]:
    url = f"{session.base_url}/_plugins/_ism/add/{index}"
    payload = {"policy_id": policy_id}
    if dry_run:
        return {"index": index, "dry_run": True, "request": payload}
    resp = session.post(url, data=json.dumps(payload))
    return {
        "index": index,
        "status_code": resp.status_code,
        "body": safe_json(resp),
    }


def attach_policy_to_existing_indices(
    session, tenant: str, policy_id: str, dry_run: bool
) -> Dict[str, Any]:
    indices = list_existing_indices(session, tenant)
    if not indices:
        return {"updated": 0, "indices": [], "message": "No indices found"}
    results = []
    for idx in indices:
        results.append(attach_policy(session, idx, policy_id, dry_run))
    return {"updated": len(results), "details": results}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Aplicar política ISM de rollover y delete por tenant.")
    p.add_argument("--tenant", required=True)
    p.add_argument(
        "--min-index-age-rollover", default="1d", help="Edad mínima para rollover (1d, 12h, 30m)"
    )
    p.add_argument("--min-size-rollover", default="50gb", help="Tamaño mínimo (50gb, 10gb...)")
    p.add_argument("--min-docs-rollover", type=int, default=10_000_000)
    p.add_argument("--delete-after-age", default="30d")
    p.add_argument("--shards", type=int, default=int(os.getenv("ISM_SHARDS", "1")))
    p.add_argument("--replicas", type=int, default=int(os.getenv("ISM_REPLICAS", "0")))
    p.add_argument(
        "--attach-existing", action="store_true", help="Adjuntar política a índices ya existentes"
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--force-update-policy",
        action="store_true",
        help="Borrar política antes de crearla (si existe)",
    )
    p.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(message)s",
    )
    session = http_client()

    # Comprobar plugin ISM
    ping = session.get(f"{session.base_url}/_plugins/_ism/policies")
    if ping.status_code not in (200, 404):
        print(
            json.dumps(
                {
                    "error": "ISM plugin no disponible o endpoint no accesible",
                    "status_code": ping.status_code,
                    "body": safe_json(ping),
                },
                indent=2,
            )
        )
        sys.exit(1)

    policy_json = build_policy(
        tenant=args.tenant,
        min_index_age_rollover=args.min_index_age_rollover,
        min_size_rollover=args.min_size_rollover,
        min_docs_rollover=args.min_docs_rollover,
        delete_after_age=args.delete_after_age,
    )
    policy_id = policy_json["policy"]["policy_id"]

    result_policy = put_policy(
        session, policy_json, dry_run=args.dry_run, force=args.force_update_policy
    )
    logging.info("policy_applied_or_dry_run")
    print(json.dumps({"policy_result": result_policy}, indent=2))

    template_json = build_index_template(
        args.tenant,
        shards=args.shards,
        replicas=args.replicas,
        policy_id=policy_id,
    )
    result_template = put_index_template(session, args.tenant, template_json, dry_run=args.dry_run)
    logging.info("template_applied_or_dry_run")
    print(json.dumps({"template_result": result_template}, indent=2))

    if args.attach_existing:
        attach_result = attach_policy_to_existing_indices(
            session, args.tenant, policy_id, dry_run=args.dry_run
        )
        logging.info("policy_attached_existing")
        print(json.dumps({"attach_existing_result": attach_result}, indent=2))


if __name__ == "__main__":
    main()
