import argparse
import json
import os
import time
from typing import Dict, Any

import pika


def fix_event(evt: Dict[str, Any], severity_default: str) -> Dict[str, Any]:
    # Completar severity nula
    if evt.get("severity") in (None, "", "null"):
        evt["severity"] = severity_default
    # Defaults mínimos
    evt.setdefault("dataset", "syslog.generic")
    evt.setdefault("schema_version", "1.0.0")
    # Asegurar @timestamp; si no existe, usar timestamp original o generar
    from datetime import datetime, timezone
    if "@timestamp" not in evt:
        evt["@timestamp"] = evt.get("timestamp", datetime.now(timezone.utc).isoformat())
    return evt


def main():
    parser = argparse.ArgumentParser(description="Reprocess messages from DLQ and republish to main exchange.")
    parser.add_argument("--host", default=os.getenv("RABBITMQ_HOST", "rabbitmq"))
    parser.add_argument("--port", type=int, default=int(os.getenv("RABBITMQ_PORT", "5672")))
    parser.add_argument("--user", default=os.getenv("RABBITMQ_USER", "admin"))
    parser.add_argument("--password", default=os.getenv("RABBITMQ_PASSWORD", "securepass"))
    parser.add_argument("--vhost", default=os.getenv("RABBITMQ_VHOST", "/"))
    parser.add_argument("--dlq", default=os.getenv("RABBITMQ_DLQ_QUEUE", "logs_siem.dlq"), help="DLQ queue name")
    parser.add_argument("--exchange", default=os.getenv("RABBITMQ_EXCHANGE", "logs_default"))
    parser.add_argument("--routing-key", default=os.getenv("RABBITMQ_ROUTING_KEY", "nubla.log.default"))
    parser.add_argument("--limit", type=int, default=100, help="Max messages to process")
    parser.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between messages")
    parser.add_argument("--dry-run", action="store_true", help="Only show transformations; do NOT publish")
    parser.add_argument("--severity-default", default="info", help="Default severity when missing")
    parser.add_argument("--verbose", action="store_true", help="Print each processed message summary")
    args = parser.parse_args()

    credentials = pika.PlainCredentials(args.user, args.password)
    params = pika.ConnectionParameters(
        host=args.host,
        port=args.port,
        virtual_host=args.vhost,
        credentials=credentials,
    )

    try:
        conn = pika.BlockingConnection(params)
    except Exception as e:
        print(json.dumps({"error": "connection_failed", "details": str(e)}))
        return

    ch = conn.channel()

    processed = 0
    requeued = 0
    published = 0
    json_errors = 0

    for i in range(args.limit):
        method, props, body = ch.basic_get(queue=args.dlq, auto_ack=False)
        if method is None:
            break  # cola vacía
        raw = body.decode("utf-8", errors="replace")

        try:
            evt = json.loads(raw)
        except Exception:
            json_errors += 1
            if args.verbose:
                print(json.dumps({"event": None, "error": "invalid_json", "raw": raw[:200]}))
            # Ack para remover de DLQ (podrías optar por requeue a otra cola de cuarentena)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            continue

        fixed = fix_event(evt, args.severity_default)

        if args.dry_run:
            requeued += 1
            # Nack con requeue True -> mensaje vuelve a la DLQ
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        else:
            ch.basic_publish(
                exchange=args.exchange,
                routing_key=args.routing_key,
                body=json.dumps(fixed, ensure_ascii=False).encode("utf-8"),
            )
            published += 1
            ch.basic_ack(delivery_tag=method.delivery_tag)

        processed += 1

        if args.verbose:
            print(json.dumps({
                "seq": i + 1,
                "tenant_id": fixed.get("tenant_id"),
                "severity_before": evt.get("severity"),
                "severity_after": fixed.get("severity"),
                "published": not args.dry_run
            }, ensure_ascii=False))

        if args.sleep > 0:
            time.sleep(args.sleep)

    conn.close()

    print(json.dumps({
        "summary": {
            "processed": processed,
            "published": published,
            "requeued_dry_run": requeued,
            "invalid_json": json_errors,
            "limit": args.limit,
            "dry_run": args.dry_run
        }
    }))


if __name__ == "__main__":
    main()