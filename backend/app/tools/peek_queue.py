#!/usr/bin/env python3
"""
Peek or consume messages from a RabbitMQ queue.

Usage examples:
  # Peek 10 messages (read and requeue -> non-destructive)
  RABBITMQ_HOST=localhost RABBITMQ_USER=admin RABBITMQ_PASSWORD=securepass \
    python backend/app/tools/peek_queue.py --queue logs_siem.dlq --count 10

  # Consume (remove) 20 messages
  python backend/app/tools/peek_queue.py --queue logs_siem.dlq --count 20 --requeue false

Notes:
- Default behavior is requeue=True (non-destructive peek).
- Prints delivery_tag, properties.headers (if any) and a preview of body.
"""
import os
import argparse
import json
import time
from typing import Any
import pika

def pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.getenv("RABBITMQ_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("RABBITMQ_PORT", "5672")))
    parser.add_argument("--user", default=os.getenv("RABBITMQ_USER", "admin"))
    parser.add_argument("--password", default=os.getenv("RABBITMQ_PASSWORD", "securepass"))
    parser.add_argument("--vhost", default=os.getenv("RABBITMQ_VHOST", "/"))
    parser.add_argument("--queue", default=os.getenv("RABBITMQ_DLQ_QUEUE", "logs_siem.dlq"))
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--requeue", type=str, default="true", choices=["true","false"], help="true -> requeue (peek), false -> consume")
    parser.add_argument("--truncate", type=int, default=1000, help="truncate body preview length")
    args = parser.parse_args()

    creds = pika.PlainCredentials(args.user, args.password)
    params = pika.ConnectionParameters(host=args.host, port=args.port, virtual_host=args.vhost, credentials=creds)

    try:
        conn = pika.BlockingConnection(params)
    except Exception as e:
        print(f"ERROR: could not connect to RabbitMQ at {args.host}:{args.port} vhost={args.vhost}: {e}")
        return

    ch = conn.channel()
    requeue = args.requeue.lower() == "true"
    print(f"Connected to {args.host}:{args.port} vhost={args.vhost} queue={args.queue} (peek={requeue})")
    processed = 0
    for i in range(args.count):
        method, props, body = ch.basic_get(queue=args.queue, auto_ack=False)
        if method is None:
            if i == 0:
                print("Queue empty or no message available right now.")
            break
        print("="*80)
        print(f"seq={i+1} delivery_tag={method.delivery_tag} redelivered={method.redelivered}")
        # headers and properties
        try:
            headers = getattr(props, "headers", None)
            print("properties.headers:", pretty(headers))
        except Exception:
            print("properties: (no headers)")
        # body preview
        try:
            body_s = body.decode("utf-8", errors="replace")
            if len(body_s) > args.truncate:
                print("body (preview):")
                print(body_s[:args.truncate] + " ... (truncated)")
            else:
                print("body:")
                print(body_s)
        except Exception:
            print("body: (binary, omitted)")
        # ack or nack (requeue)
        if requeue:
            # put it back to the queue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        else:
            # remove from queue
            ch.basic_ack(delivery_tag=method.delivery_tag)
        processed += 1
        # small sleep to avoid hammering broker if large count
        time.sleep(0.05)
    conn.close()
    print(f"Done. Processed: {processed}. (requeue={requeue})")

if __name__ == "__main__":
    main()