#!/usr/bin/env python
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("apply_policies")

OS_HOST = os.getenv("OPENSEARCH_HOST", "http://localhost:9201")
OS_USER = os.getenv("OS_USER", "admin")
OS_PASS = os.getenv("OS_PASS", "admin")
APPLY_FORCE = os.getenv("APPLY_POLICIES_FORCE", "0") in ("1", "true", "True")

POLICIES_DIR = Path("policies")
TENANTS_FILE = Path("config/tenants.json")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_tenants(raw) -> List[Dict[str, Any]]:
    """
    Acepta:
    - {"tenants":[...]}
    - [...]
    Devuelve lista de tenants.
    """
    if isinstance(raw, dict):
        if "tenants" in raw and isinstance(raw["tenants"], list):
            return raw["tenants"]
        else:
            raise ValueError("El objeto JSON debe tener clave 'tenants' con una lista.")
    elif isinstance(raw, list):
        return raw
    else:
        raise ValueError("Formato de tenants.json no reconocido.")


def policy_hash(policy_block: Dict[str, Any]) -> str:
    """
    Hash simple para comparar políticas.
    """
    return hashlib.sha256(json.dumps(policy_block, sort_keys=True).encode()).hexdigest()


def get_existing_policy(policy_id: str):
    url = f"{OS_HOST}/_plugins/_ism/policies/{policy_id}"
    r = requests.get(url, auth=(OS_USER, OS_PASS))
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        LOG.error("policy_get_failed id=%s status=%s body=%s", policy_id, r.status_code, r.text)
        return None
    data = r.json()
    return {
        "seq_no": data.get("_seq_no"),
        "primary_term": data.get("_primary_term"),
        "policy": data.get("policy"),
    }


def upsert_policy(policy_path: Path):
    data = load_json(policy_path)
    if "policy" not in data:
        LOG.error("invalid_policy_file_missing_policy_key file=%s", policy_path)
        return

    policy_id = data["policy"]["policy_id"]
    existing = get_existing_policy(policy_id)

    new_hash = policy_hash(data["policy"])

    if existing:
        old_hash = policy_hash(existing["policy"])
        if old_hash == new_hash and not APPLY_FORCE:
            LOG.info("policy_unchanged_skip id=%s", policy_id)
            return
        # Update with concurrency control
        seq = existing["seq_no"]
        pt = existing["primary_term"]
        url = f"{OS_HOST}/_plugins/_ism/policies/{policy_id}?if_seq_no={seq}&if_primary_term={pt}"
        r = requests.put(url, auth=(OS_USER, OS_PASS), json=data)
        if r.status_code not in (200, 201):
            LOG.error(
                "policy_update_failed id=%s status=%s body=%s", policy_id, r.status_code, r.text
            )
        else:
            LOG.info("policy_updated id=%s", policy_id)
    else:
        # Create new
        url = f"{OS_HOST}/_plugins/_ism/policies/{policy_id}"
        r = requests.put(url, auth=(OS_USER, OS_PASS), json=data)
        if r.status_code not in (200, 201):
            LOG.error(
                "policy_create_failed id=%s status=%s body=%s", policy_id, r.status_code, r.text
            )
        else:
            LOG.info("policy_created id=%s", policy_id)


def ensure_index_and_alias(tenant: Dict[str, Any]):
    tid = tenant["id"]
    alias = tenant.get("rollover_alias", f"logs-{tid}")
    policy_id = tenant["policy_id"]
    index_initial = f"{alias}-000001"

    # 1. Índice inicial
    r_exists = requests.get(f"{OS_HOST}/{index_initial}", auth=(OS_USER, OS_PASS))
    if r_exists.status_code == 404:
        r_create = requests.put(
            f"{OS_HOST}/{index_initial}",
            auth=(OS_USER, OS_PASS),
            json={
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "opendistro": {
                        "index_state_management": {"rollover_alias": alias, "policy_id": policy_id}
                    },
                }
            },
        )
        if r_create.status_code not in (200, 201):
            LOG.error(
                "index_create_failed tenant=%s status=%s body=%s",
                tid,
                r_create.status_code,
                r_create.text,
            )
            return
        LOG.info("index_created tenant=%s index=%s", tid, index_initial)
    else:
        LOG.info("index_exists tenant=%s index=%s", tid, index_initial)

        # Asegurar settings rollover_alias (idempotente)
        r_set = requests.put(
            f"{OS_HOST}/{index_initial}/_settings",
            auth=(OS_USER, OS_PASS),
            json={"index": {"opendistro.index_state_management.rollover_alias": alias}},
        )
        if r_set.status_code not in (200, 201):
            LOG.warning(
                "rollover_alias_set_failed tenant=%s status=%s body=%s",
                tid,
                r_set.status_code,
                r_set.text,
            )
        else:
            LOG.info("rollover_alias_ok tenant=%s alias=%s", tid, alias)

    # 2. Alias write
    r_alias = requests.post(
        f"{OS_HOST}/_aliases",
        auth=(OS_USER, OS_PASS),
        json={
            "actions": [{"add": {"index": index_initial, "alias": alias, "is_write_index": True}}]
        },
    )
    if r_alias.status_code not in (200, 201):
        LOG.warning(
            "alias_add_failed_or_exists tenant=%s status=%s body=%s",
            tid,
            r_alias.status_code,
            r_alias.text,
        )
    else:
        LOG.info("alias_write_ok tenant=%s alias=%s", tid, alias)

    # 3. Adjuntar política (add) — si no estaba aplicada
    r_add = requests.post(
        f"{OS_HOST}/_plugins/_ism/add/{index_initial}",
        auth=(OS_USER, OS_PASS),
        json={"policy_id": policy_id},
    )
    if r_add.status_code not in (200, 201):
        LOG.warning(
            "policy_attach_failed tenant=%s policy_id=%s status=%s body=%s",
            tid,
            policy_id,
            r_add.status_code,
            r_add.text,
        )
    else:
        LOG.info("policy_attach_ok tenant=%s policy_id=%s", tid, policy_id)


def main():
    # Publicar políticas (todas las .json en policies/)
    for policy_file in POLICIES_DIR.glob("ism_*.json"):
        upsert_policy(policy_file)

    # Cargar tenants
    if not TENANTS_FILE.exists():
        LOG.error("tenants_file_missing path=%s", TENANTS_FILE)
        return

    raw_tenants = load_json(TENANTS_FILE)
    try:
        tenants = normalize_tenants(raw_tenants)
    except ValueError as e:
        LOG.error("tenants_file_invalid error=%s", e)
        return

    for t in tenants:
        if not t.get("active", True):
            LOG.info("tenant_inactive_skip id=%s", t.get("id"))
            continue
        ensure_index_and_alias(t)


if __name__ == "__main__":
    main()
