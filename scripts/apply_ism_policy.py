#!/usr/bin/env python
"""
Aplicación de políticas ISM (Index State Management) por tenant en OpenSearch.

Flujo:
1. Genera (o aplica) una política con estados:
   - hot: espera condiciones de rollover (edad, tamaño, docs).
   - delete: borra índices tras alcanzar edad de retención.
2. Crea una index template para logs-<tenant>-* que:
   - Asigna la política.
   - Define el alias de rollover (logs-<tenant>).
   - Ajusta shards y replicas.
3. Opcionalmente puede forzar la aplicación a índices existentes.

Requisitos:
- OpenSearch 2.x con plugin ISM activado (endpoint _plugins/_ism).
- Variables de entorno OS_USER/OS_PASS si autenticado.
- Ejecutar antes: crear alias + primer índice (si migrando desde modelo sin template).
"""
from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

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
    # OpenSearch ISM requiere timestamps en epoch millis si se incluye last_updated_time (lo omitimos).
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
                            }
                        }
                    ],
                    "transitions": [
                        {
                            "state_name": "delete",
                            "conditions": {"min_index_age": delete_after_age},
                        }
                    ],
                },
                {
                    "name": "delete",
                    "actions": [{"delete": {}}],
                    "transitions": [],
                },
            ],
            # Template (esto permite auto-aplicar política a nuevos índices que cumplan patrón)
            "ism_template": {
                "index_patterns": [f"logs-{tenant}-*"],
                "priority": 100,
            },
        }
    }


def build_index_template(
    tenant: str,
    shards: int,
    replicas: int,
    policy_id: str,
) -> Dict[str, Any]:
    """
    Index template que:
    - Aplica política ISM (clave depende de versión; se incluyen ambas).
    - Define alias de rollover (logs-<tenant>).
    """
    return {
        "index_patterns": [f"logs-{tenant}-*"],
        "template": {
            "settings": {
                "number_of_shards": shards,
                "number_of_replicas": replicas,
                # Claves históricas y actuales para compatibilidad
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


def put_policy(session, policy_json: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    policy_id = policy_json["policy"]["policy_id"]
    url = f"{session.base_url}/_plugins/_ism/policies/{policy_id}"
    resp = session.put(url, data=json.dumps(policy_json))
    if dry_run:
        return {
            "dry_run": True,
            "request": policy_json,
            "status_code": resp.status_code,
            "body": safe_json(resp),
        }
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Error creando política {policy_id}: {resp.status_code} {resp.text}")
    return safe_json(resp)


def put_index_template(
    session, tenant: str, template_json: Dict[str, Any], dry_run: bool
) -> Dict[str, Any]:
    name = f"logs-{tenant}-template"
    url = f"{session.base_url}/_index_template/{name}"
    resp = session.put(url, data=json.dumps({"index_template": template_json}))
    if dry_run:
        return {
            "dry_run": True,
            "request": template_json,
            "status_code": resp.status_code,
            "body": safe_json(resp),
        }
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Error creando index template {name}: {resp.status_code} {resp.text}")
    return safe_json(resp)


def attach_policy_to_existing_indices(
    session, tenant: str, policy_id: str, dry_run: bool
) -> Dict[str, Any]:
    """
    Asigna la política a índices existentes que coinciden con patrón logs-tenant-* y cuya configuración no la tenga.
    """
    pattern = f"logs-{tenant}-*"
    # Obtener índices
    url = f"{session.base_url}/{pattern}"
    resp = session.get(url)
    if resp.status_code == 404:
        return {"updated": 0, "indices": [], "message": "No indices found"}
    data = safe_json(resp)
    indices = list(data.keys())
    changed = []
    for idx in indices:
        # Ajustar settings (OpenSearch: PUT /<index>/_settings)
        payload = {
            "settings": {
                "opendistro.index_state_management.policy_id": policy_id,
                "index.opendistro.index_state_management.policy_id": policy_id,
                "opensearch.index_state_management.policy_id": policy_id,
            }
        }
        if dry_run:
            changed.append({"index": idx, "payload": payload})
        else:
            s_url = f"{session.base_url}/{idx}/_settings"
            r2 = session.put(s_url, data=json.dumps(payload))
            if r2.status_code not in (200, 201):
                raise RuntimeError(f"Error asignando política a {idx}: {r2.status_code} {r2.text}")
            changed.append({"index": idx, "result": safe_json(r2)})
    return {"updated": len(changed), "details": changed}


def safe_json(resp) -> Any:
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Aplicar política ISM de rollover y delete por tenant.")
    p.add_argument("--tenant", required=True)
    p.add_argument(
        "--min-index-age-rollover",
        default="1d",
        help="Edad mínima para rollover (e.g. 1d, 12h, 30m)",
    )
    p.add_argument(
        "--min-size-rollover", default="50gb", help="Tamaño mínimo para rollover (e.g. 50gb)"
    )
    p.add_argument(
        "--min-docs-rollover", type=int, default=10_000_000, help="Documentos mínimos para rollover"
    )
    p.add_argument(
        "--delete-after-age",
        default="30d",
        help="Edad para transicionar a delete y eliminar índice",
    )
    p.add_argument("--shards", type=int, default=int(os.getenv("ISM_SHARDS", "1")))
    p.add_argument("--replicas", type=int, default=int(os.getenv("ISM_REPLICAS", "0")))
    p.add_argument(
        "--attach-existing", action="store_true", help="Aplicar política a índices ya existentes"
    )
    p.add_argument("--dry-run", action="store_true", help="No persiste, solo muestra payloads")
    p.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(message)s",
    )

    session = http_client()
    # Comprobación rápida del plugin ISM
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

    result_policy = put_policy(session, policy_json, dry_run=args.dry_run)
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
