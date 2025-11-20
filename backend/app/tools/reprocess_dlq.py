#!/usr/bin/env python3
"""
Reprocess DLQ with normalization and optional reject reason annotation.
Defaults updated to nubla_logs_default.dlq.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any, Dict, Optional

import pika

# Normalizador: intentar fully-qualified y relativo; fallback passthrough
try:
    from backend.app.processing.normalizer import normalize  # type: ignore
except Exception:
    try:
        from processing.normalizer import normalize  # type: ignore
    except Exception:

        def normalize(x: Dict[str, Any]) -> Dict[str, Any]:
            return x


def fix_event(evt: Dict[str, Any], severity_default: str) -> Dict[str, Any]:
    out = dict(evt)
    if out.get("severity") in (None, "", "null"):
        out["severity"] = severity_default
    out.setdefault("dataset", "syslog.generic")
    out.setdefault("schema_version", "1.0.0")
    if "@timestamp" not in out and "timestamp" in out:
        out["@timestamp"] = out["timestamp"]
    return out


def publish_event(
    ch, exchange: str, routing_key: str, body: Dict[str, Any], reason: Optional[str] = None
) -> None:
    props = None
    if reason:
        try:
            props = pika.BasicProperties(headers={"x-reprocess-reason": reason})
        except Exception:
            pass
    ch.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        properties=props,
    )


def main() -> None:
    p = argparse.ArgumentParser(
        description="Reprocess messages from DLQ and republish to main exchange with normalization."
    )
    p.add_argument("--host", default=os.getenv("RABBITMQ_HOST", "rabbitmq"))
    p.add_argument("--port", type=int, default=int(os.getenv("RABBITMQ_PORT", "5672")))
    p.add_argument("--user", default=os.getenv("RABBITMQ_USER", "admin"))
    p.add_argument("--password", default=os.getenv("RABBITMQ_PASSWORD", "securepass"))
    p.add_argument("--vhost", default=os.getenv("RABBITMQ_VHOST", "/"))
    p.add_argument("--dlq", default=os.getenv("RABBITMQ_DLQ", "nubla_logs_default.dlq"))
    p.add_argument("--exchange", default=os.getenv("RABBITMQ_EXCHANGE", "logs_default"))
    p.add_argument("--routing-key", default=os.getenv("RABBITMQ_ROUTING_KEY", "nubla.log.default"))
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--sleep", type=float, default=0.0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--severity-default", default="info")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--quarantine", default="")
    p.add_argument("--reject-reason-field", default="dlq_reprocess")
    args = p.parse_args()

    credentials = pika.PlainCredentials(args.user, args.password)
    params = pika.ConnectionParameters(
        host=args.host, port=args.port, virtual_host=args.vhost, credentials=credentials
    )

    try:
        conn = pika.BlockingConnection(params)
    except Exception as e:
        print(json.dumps({"error": "connection_failed", "details": str(e)}))
        return

    ch = conn.channel()

    processed = 0
    published = 0
    requeued_dry = 0
    invalid_json = 0
    quarantined = 0

    for i in range(args.limit):
        method, props, body = ch.basic_get(queue=args.dlq, auto_ack=False)
        if method is None:
            break

        raw = body.decode("utf-8", errors="replace")
        evt: Optional[Dict[str, Any]] = None
        try:
            evt = json.loads(raw)
        except Exception:
            invalid_json += 1
            if args.quarantine:
                if not args.dry_run:
                    ch.basic_publish(exchange="", routing_key=args.quarantine, body=body)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    quarantined += 1
                else:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    requeued_dry += 1
            else:
                if args.dry_run:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    requeued_dry += 1
                else:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            if args.verbose:
                print(
                    json.dumps(
                        {"seq": i + 1, "status": "invalid_json", "preview": raw[:300]},
                        ensure_ascii=False,
                    )
                )
            processed += 1
            if args.sleep:
                time.sleep(args.sleep)
            continue

        try:
            structured = normalize(evt)
        except Exception:
            structured = fix_event(evt, args.severity_default)

        if structured.get("tenant_id") in (None, ""):
            structured["tenant_id"] = "default"
        structured = fix_event(structured, args.severity_default)

        # Marca el evento reprocesado con un campo booleano configurable (por defecto: dlq_reprocess)
        structured[args.reject_reason_field] = (
            True  # <= FIX: usar atributo con guion convertido a subrayado
        )

        if args.dry_run:
            requeued_dry += 1
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            if args.verbose:
                print(
                    json.dumps(
                        {
                            "seq": i + 1,
                            "tenant_id": structured.get("tenant_id"),
                            "severity_after": structured.get("severity"),
                            "published": False,
                            "preview": {
                                k: structured.get(k) for k in ("host", "@timestamp", "message")
                            },
                        },
                        ensure_ascii=False,
                    )
                )
        else:
            try:
                publish_event(
                    ch, args.exchange, args.routing_key, structured, reason="dlq_reprocess"
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                published += 1
                if args.verbose:
                    print(
                        json.dumps(
                            {
                                "seq": i + 1,
                                "tenant_id": structured.get("tenant_id"),
                                "severity_after": structured.get("severity"),
                                "published": True,
                                "preview": {
                                    k: structured.get(k) for k in ("host", "@timestamp", "message")
                                },
                            },
                            ensure_ascii=False,
                        )
                    )
            except Exception as e:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                if args.verbose:
                    print(json.dumps({"seq": i + 1, "error": str(e)}))
        processed += 1
        if args.sleep:
            time.sleep(args.sleep)

    conn.close()
    print(
        json.dumps(
            {
                "summary": {
                    "processed": processed,
                    "published": published,
                    "requeued_dry_run": requeued_dry,
                    "invalid_json": invalid_json,
                    "quarantined": quarantined,
                    "limit": args.limit,
                    "dry_run": bool(args.dry_run),
                }
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
