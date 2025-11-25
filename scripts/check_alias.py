#!/usr/bin/env python
import os
import sys
import requests

OS_HOST = os.getenv("OPENSEARCH_HOST", "http://localhost:9201")
OS_USER = os.getenv("OS_USER", "admin")
OS_PASS = os.getenv("OS_PASS", "admin")

ALIAS = os.getenv("CHECK_ALIAS", "logs-default")

def main():
    r = requests.get(f"{OS_HOST}/_alias/{ALIAS}", auth=(OS_USER, OS_PASS))
    if r.status_code != 200:
        print(f"ALIAS_FETCH_ERROR status={r.status_code} body={r.text}")
        sys.exit(2)
    data = r.json()
    write_indices = []
    for idx, meta in data.items():
        if meta.get("aliases", {}).get(ALIAS, {}).get("is_write_index") is True:
            write_indices.append(idx)
    if len(write_indices) != 1:
        print(f"ALIAS_WRITE_INDEX_INVALID alias={ALIAS} write_indices={write_indices}")
        sys.exit(1)
    print(f"ALIAS_WRITE_INDEX_OK alias={ALIAS} write_index={write_indices[0]}")
    sys.exit(0)

if __name__ == "__main__":
    main()