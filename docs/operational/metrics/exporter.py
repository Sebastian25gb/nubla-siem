#!/usr/bin/env python3
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen

OS_URL = os.getenv("OS_URL", "http://localhost:9201")
ALIAS = os.getenv("LOGS_ALIAS", "logs-default")
PORT = int(os.getenv("PORT", "9108"))


def os_search(body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = Request(f"{OS_URL}/{ALIAS}/_search", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_metrics() -> str:
    # Total docs
    total = os_search({"size": 0})
    total_docs = total.get("hits", {}).get("total", {}).get("value", 0)

    # By severity (keyword)
    by_sev = os_search({"size": 0, "aggs": {"sev": {"terms": {"field": "severity", "size": 10}}}})
    sev_buckets = by_sev.get("aggregations", {}).get("sev", {}).get("buckets", [])

    # Last 1h
    last1h = os_search(
        {"size": 0, "query": {"range": {"@timestamp": {"gte": "now-1h", "lte": "now"}}}}
    )
    last1h_docs = last1h.get("hits", {}).get("total", {}).get("value", 0)

    # Prometheus text format
    lines = []
    lines.append("# HELP nubla_logs_docs_total Total documents in alias")
    lines.append("# TYPE nubla_logs_docs_total gauge")
    lines.append(f'nubla_logs_docs_total{{alias="{ALIAS}"}} {total_docs}')

    lines.append("# HELP nubla_logs_docs_severity Documents by severity")
    lines.append("# TYPE nubla_logs_docs_severity gauge")
    for b in sev_buckets:
        s = b.get("key", "")
        v = b.get("doc_count", 0)
        lines.append(f'nubla_logs_docs_severity{{alias="{ALIAS}",severity="{s}"}} {v}')

    lines.append("# HELP nubla_logs_docs_last_hour Documents ingested in last hour")
    lines.append("# TYPE nubla_logs_docs_last_hour gauge")
    lines.append(f'nubla_logs_docs_last_hour{{alias="{ALIAS}"}} {last1h_docs}')

    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
    # Dentro de la clase Handler(BaseHTTPRequestHandler) -> método do_GET
    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")
            return
        try:
            body = build_metrics().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"error")


def main():
    srv = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"metrics exporter listening on :{PORT} (alias={ALIAS}, os={OS_URL})")
    srv.serve_forever()


if __name__ == "__main__":
    main()
