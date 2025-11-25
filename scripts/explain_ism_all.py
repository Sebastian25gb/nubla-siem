#!/usr/bin/env python
import os, requests, sys, json

OS_HOST = os.getenv("OPENSEARCH_HOST", "http://localhost:9201")
OS_USER = os.getenv("OS_USER", "admin")
OS_PASS = os.getenv("OS_PASS", "admin")

def main():
    r = requests.get(f"{OS_HOST}/_cat/indices?h=index", auth=(OS_USER, OS_PASS))
    if r.status_code != 200:
        print(json.dumps({"error": "indices_fetch_failed", "status": r.status_code, "body": r.text}))
        sys.exit(2)
    indices = [i.strip() for i in r.text.splitlines() if i.startswith("logs-")]
    report = {}
    for idx in indices:
        er = requests.get(f"{OS_HOST}/_plugins/_ism/explain/{idx}", auth=(OS_USER, OS_PASS))
        if er.status_code != 200:
            report[idx] = {"error": er.status_code, "body": er.text}
            continue
        data = er.json().get(idx, {})
        report[idx] = {
            "policy_id": data.get("policy_id") or data.get("index.plugins.index_state_management.policy_id"),
            "managed": data.get("enabled"),
            "rolled_over": data.get("rolled_over"),
            "message": (data.get("info") or {}).get("message")
        }
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
