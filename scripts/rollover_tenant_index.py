#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import logging
import os
from typing import Any, Dict, List, Optional

from opensearchpy import NotFoundError  # type: ignore

# Reutilizamos la conexión del backend
try:
    from backend.app.repository.elastic import get_es
except Exception:
    # Fallback simple si se usa el script fuera del entorno del backend
    from opensearchpy import OpenSearch  # type: ignore

    def _normalize_url(raw: Optional[str]) -> str:
        fallback = "http://opensearch:9200"
        raw = (raw or "").strip()
        if not raw:
            return fallback
        if raw.startswith(("http://", "https://")):
            return raw
        if ":" in raw:
            return f"http://{raw}"
        return f"http://{raw}:9200"

    def _get_auth():
        user = os.getenv("OS_USER") or os.getenv("ES_USER")
        pwd = os.getenv("OS_PASS") or os.getenv("ES_PASS")
        if user and pwd:
            return (user, pwd)
        return None

    def get_es():
        raw = os.getenv("OPENSEARCH_HOST") or os.getenv("ELASTICSEARCH_HOST") or "opensearch:9200"
        url = _normalize_url(raw)
        auth = _get_auth()
        kwargs: Dict[str, Any] = {"hosts": [url], "timeout": 30}
        if auth:
            kwargs["http_auth"] = auth
        client = OpenSearch(**kwargs)
        client.info()
        return client


logger = logging.getLogger("rollover")


def index_name_for(tenant: str, seq: int) -> str:
    return f"logs-{tenant}-{seq:06d}"


def alias_for(tenant: str) -> str:
    return f"logs-{tenant}"


def get_alias_indices(es, alias: str) -> List[str]:
    try:
        data = es.indices.get_alias(name=alias)  # type: ignore
        return sorted(list(data.keys()))
    except NotFoundError:
        return []
    except Exception as e:
        logger.error("get_alias_failed", extra={"alias": alias, "error": str(e)})
        raise


def ensure_initial_index_and_alias(
    es,
    tenant: str,
    shards: int = 1,
    replicas: int = 0,
) -> str:
    a = alias_for(tenant)
    indices = get_alias_indices(es, a)
    if indices:
        # Asegura que exista write_index
        ensure_write_index_flag(es, a, indices[-1], indices)
        logger.info("alias_exists", extra={"alias": a, "indices": indices})
        return indices[-1]

    # Crear índice inicial y alias con write_index
    first = index_name_for(tenant, 1)
    body = {
        "settings": {
            "number_of_shards": shards,
            "number_of_replicas": replicas,
        }
    }
    es.indices.create(index=first, body=body)  # type: ignore
    es.indices.put_alias(index=first, name=a, body={"is_write_index": True})  # type: ignore
    logger.info("alias_initialized", extra={"alias": a, "index": first})
    return first


def ensure_write_index_flag(
    es, alias: str, write_index: str, all_indices: Optional[List[str]] = None
) -> None:
    if all_indices is None:
        all_indices = get_alias_indices(es, alias)
    actions: List[Dict[str, Any]] = []

    # Quitar is_write_index de todos
    for idx in all_indices:
        actions.append({"remove": {"index": idx, "alias": alias, "must_exist": False}})

    # Volver a agregarlos sin flag, y al write_index con flag
    for idx in all_indices:
        if idx == write_index:
            actions.append({"add": {"index": idx, "alias": alias, "is_write_index": True}})
        else:
            actions.append({"add": {"index": idx, "alias": alias}})

    if actions:
        es.indices.update_aliases({"actions": actions})  # type: ignore
        logger.info("write_index_set", extra={"alias": alias, "write_index": write_index})


def next_sequence_from(indices: List[str], tenant: str) -> int:
    # Busca el mayor sufijo numérico logs-<tenant>-000123 -> 123
    seq = 0
    prefix = f"logs-{tenant}-"
    for idx in indices:
        if idx.startswith(prefix):
            try:
                num = int(idx[len(prefix) :])
                seq = max(seq, num)
            except ValueError:
                pass
    return seq + 1


def do_rollover(
    es,
    tenant: str,
    max_docs: Optional[int],
    max_size: Optional[str],
    max_age: Optional[str],
    dry_run: bool,
) -> Dict[str, Any]:
    a = alias_for(tenant)
    # Asegura que haya alias e índice inicial
    ensure_initial_index_and_alias(es, tenant)
    conditions: Dict[str, Any] = {}
    if max_docs is not None:
        conditions["max_docs"] = max_docs
    if max_size:
        conditions["max_size"] = max_size
    if max_age:
        conditions["max_age"] = max_age
    body = {"conditions": conditions or {"max_docs": 1_000_000}}

    # opensearch-py rollover: es.indices.rollover(alias=..., body=..., dry_run=True/False)
    resp = es.indices.rollover(alias=a, body=body, dry_run=dry_run)  # type: ignore
    return resp


def check_status(es, tenant: str) -> Dict[str, Any]:
    a = alias_for(tenant)
    data: Dict[str, Any] = {"alias": a, "indices": []}
    indices = get_alias_indices(es, a)
    data["indices"] = indices
    if indices:
        # Detectar cuál es write_index
        alias_data = es.indices.get_alias(name=a)  # type: ignore
        write = None
        for idx, aliases in alias_data.items():
            info = aliases.get("aliases", {}).get(a, {})
            if info.get("is_write_index") is True:
                write = idx
                break
        data["write_index_current"] = write or indices[-1]
    return data


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Rollover de índices por tenant (OpenSearch/Elasticsearch)."
    )
    p.add_argument("--tenant", required=True, help="ID del tenant (p.ej., delawarehotel)")
    p.add_argument("--init", action="store_true", help="Crear alias e índice inicial si no existen")
    p.add_argument("--check", action="store_true", help="Mostrar estado actual del alias e índices")
    p.add_argument("--rollover", action="store_true", help="Ejecutar rollover según condiciones")
    p.add_argument("--dry-run", action="store_true", help="Simular rollover sin crear índice nuevo")
    p.add_argument("--max-docs", type=int, default=None, help="Condición: máximo de documentos")
    p.add_argument(
        "--max-size", type=str, default=None, help="Condición: tamaño máximo (e.g., 50gb)"
    )
    p.add_argument(
        "--max-age", type=str, default=None, help="Condición: antigüedad máxima (e.g., 7d)"
    )
    p.add_argument(
        "--shards",
        type=int,
        default=int(os.getenv("ROLLOVER_SHARDS", "1")),
        help="Shards del índice inicial",
    )
    p.add_argument(
        "--replicas",
        type=int,
        default=int(os.getenv("ROLLOVER_REPLICAS", "0")),
        help="Replicas del índice inicial",
    )
    p.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO), format="%(message)s"
    )
    es = get_es()

    if args.init:
        idx = ensure_initial_index_and_alias(
            es, args.tenant, shards=args.shards, replicas=args.replicas
        )
        print(
            json.dumps(
                {"initialized": True, "index": idx, "alias": alias_for(args.tenant)}, indent=2
            )
        )

    if args.check:
        status = check_status(es, args.tenant)
        print(json.dumps(status, indent=2))

    if args.rollover:
        resp = do_rollover(
            es,
            tenant=args.tenant,
            max_docs=args.max_docs,
            max_size=args.max_size,
            max_age=args.max_age,
            dry_run=args.dry_run,
        )
        print(json.dumps(resp, indent=2))


if __name__ == "__main__":
    main()
