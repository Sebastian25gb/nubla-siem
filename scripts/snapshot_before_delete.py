#!/usr/bin/env python
import logging
import os
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("snapshot_before_delete")

OS_HOST = os.getenv("OPENSEARCH_HOST", "http://localhost:9201")
OS_USER = os.getenv("OS_USER", "admin")
OS_PASS = os.getenv("OS_PASS", "admin")
REPO = os.getenv("SNAPSHOT_REPO", "dev_backup")
ALIAS = os.getenv("TARGET_ALIAS", "logs-default")


def list_indices_for_alias():
    r = requests.get(f"{OS_HOST}/_alias/{ALIAS}", auth=(OS_USER, OS_PASS))
    if r.status_code != 200:
        LOG.error("alias_fetch_failed status=%s body=%s", r.status_code, r.text)
        return []
    return list(r.json().keys())


def explain(index):
    r = requests.get(f"{OS_HOST}/_plugins/_ism/explain/{index}", auth=(OS_USER, OS_PASS))
    if r.status_code != 200:
        LOG.warning("explain_failed index=%s status=%s", index, r.status_code)
        return None
    return r.json().get(index)


def snapshot_index(index):
    snap_name = f"snap_{index}_{int(time.time())}"
    r = requests.put(
        f"{OS_HOST}/_snapshot/{REPO}/{snap_name}",
        auth=(OS_USER, OS_PASS),
        json={"indices": index, "include_global_state": False},
    )
    if r.status_code not in (200, 201):
        LOG.error("snapshot_failed index=%s status=%s body=%s", index, r.status_code, r.text)
    else:
        LOG.info("snapshot_ok index=%s snapshot=%s", index, snap_name)


def main():
    indices = list_indices_for_alias()
    for idx in indices:
        info = explain(idx)
        if not info:
            continue
        # Cuando el índice esté por entrar a estado delete (ejemplo: edad >= 6d)
        age_condition = info.get("info", {}).get("conditions", {}).get("min_index_age", {})
        current_age_str = age_condition.get("current")
        # current_age_str: "4.9d" etc. Simple heurística:
        if current_age_str and current_age_str.endswith("d"):
            days = float(current_age_str[:-1])
            if days >= 6.0:  # umbral antes de delete a 7d
                snapshot_index(idx)


if __name__ == "__main__":
    main()
