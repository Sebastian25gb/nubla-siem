#!/usr/bin/env python3
"""
Smoke test Nubla SIEM:
1. Publica evento válido -> espera index (severity en minúsculas si pipeline activo).
2. Publica evento inválido -> espera en DLQ (rejected).
3. Imprime JSON resumen.
Exit code 0 si pasa; 1 si falla alguna condición básica.
"""
import json
import os
import sys
import time

import pika
import requests


def env(name, default=None):
    return os.getenv(name, default)


host_rmq = env("RABBITMQ_HOST", "127.0.0.1")
user_rmq = env("RABBITMQ_USER", "admin")
pass_rmq = env("RABBITMQ_PASSWORD", "securepass")
exchange = env("RABBITMQ_EXCHANGE", "logs_default")
rk = env("RABBITMQ_ROUTING_KEY", "nubla.log.default")
dlq = env("RABBITMQ_DLQ", "nubla_logs_default.dlq")
index = env("LOGS_INDEX", "logs-default")
search_host = env("ELASTICSEARCH_HOST", "127.0.0.1:9201").strip()
base_url = search_host if search_host.startswith("http") else f"http://{search_host}"

creds = pika.PlainCredentials(user_rmq, pass_rmq)
conn = pika.BlockingConnection(pika.ConnectionParameters(host_rmq, 5672, credentials=creds))
ch = conn.channel()

valid = {
    "tenant_id": "default",
    "@timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "dataset": "syslog.generic",
    "schema_version": "1.0.0",
    "severity": "HIGH",
    "message": "smoke test event",
}
invalid = {"message": "incomplete"}

ch.basic_publish(exchange=exchange, routing_key=rk, body=json.dumps(valid).encode())
ch.basic_publish(exchange=exchange, routing_key=rk, body=json.dumps(invalid).encode())
conn.close()

time.sleep(2.5)

# Query index
try:
    r = requests.get(f"{base_url}/{index}/_search", params={"size": 2, "sort": "@timestamp:desc"})
    r.raise_for_status()
    hits = r.json().get("hits", {}).get("hits", [])
    indexed = [h.get("_source") for h in hits]
except Exception:
    indexed = []

# DLQ read (requeue to leave messages intact)
try:
    rdlq = requests.post(
        f"http://{host_rmq}:15672/api/queues/%2F/{dlq}/get",
        auth=(user_rmq, pass_rmq),
        headers={"content-type": "application/json"},
        data=json.dumps(
            {"count": 10, "ackmode": "ack_requeue_true", "encoding": "auto", "truncate": 50000}
        ),
    )
    dlq_msgs = rdlq.json()
except Exception:
    dlq_msgs = []

invalid_present = any(
    "incomplete"
    in (
        json.loads(m.get("payload", "{}")).get("message", "")
        if isinstance(m.get("payload"), str)
        else ""
    )
    for m in dlq_msgs
)

severity_lower_ok = any(doc.get("severity") == "high" for doc in indexed)

result = {
    "indexed_count": len(indexed),
    "severity_lowercase": severity_lower_ok,
    "invalid_in_dlq": invalid_present,
    "dlq_count_sample": len(dlq_msgs),
    "pass": bool(severity_lower_ok and invalid_present),
}

print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if result["pass"] else 1)
