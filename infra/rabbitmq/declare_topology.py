#!/usr/bin/env python3
"""
Topología canónica RabbitMQ (single-tenant):
(Actualizado para aceptar RABBITMQ_USER/PASSWORD además de RABBIT_USER/PASS)
"""
import os
import sys
import pika
from pika.exceptions import ChannelClosedByBroker

RABBIT_HOST = os.environ.get("RABBIT_HOST", "127.0.0.1")
RABBIT_PORT = int(os.environ.get("RABBIT_PORT", "5672"))
RABBIT_VHOST = os.environ.get("RABBIT_VHOST", "/")
USER = os.environ.get("RABBIT_USER") or os.environ.get("RABBITMQ_USER")
PASSWORD = os.environ.get("RABBIT_PASS") or os.environ.get("RABBITMQ_PASSWORD")

EXCHANGE = os.environ.get("RABBITMQ_EXCHANGE", "logs_default")
DLX = os.environ.get("RABBITMQ_DLX", "logs_default.dlx")
QUEUE = os.environ.get("RABBITMQ_QUEUE", "nubla_logs_default")
DLQ = os.environ.get("RABBITMQ_DLQ", "nubla_logs_default.dlq")
ROUTING_KEY = os.environ.get("RABBITMQ_ROUTING_KEY", "nubla.log.default")
FORCE_RECREATE = os.environ.get("FORCE_RECREATE", "false").lower() == "true"

if not USER or not PASSWORD:
    print("ERROR: Define RABBITMQ_USER/RABBITMQ_PASSWORD (o RABBIT_USER/RABBIT_PASS)")
    sys.exit(1)

creds = pika.PlainCredentials(USER, PASSWORD)
params = pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT, virtual_host=RABBIT_VHOST, credentials=creds)
conn = pika.BlockingConnection(params)
ch = conn.channel()

def ensure_exchange(name: str, durable: bool = True, ex_type: str = "topic"):
    try:
        ch.exchange_declare(exchange=name, passive=True)
        ch.exchange_declare(exchange=name, exchange_type=ex_type, durable=durable)
        return ch
    except ChannelClosedByBroker:
        new_ch = conn.channel()
        new_ch.exchange_declare(exchange=name, exchange_type=ex_type, durable=durable)
        return new_ch

def ensure_queue(name: str, args: dict | None = None):
    args = args or {}
    try:
        ch.queue_declare(queue=name, passive=True)
        ch.queue_declare(queue=name, durable=True, arguments=args)
        return ch
    except ChannelClosedByBroker:
        new_ch = conn.channel()
        new_ch.queue_declare(queue=name, durable=True, arguments=args)
        return new_ch

ch = ensure_exchange(EXCHANGE)
print(f"exchange {EXCHANGE} OK")
ch = ensure_exchange(DLX)
print(f"exchange {DLX} OK")

ch = ensure_queue(DLQ)
print(f"queue {DLQ} OK")
ch = ensure_queue(QUEUE, args={"x-dead-letter-exchange": DLX})
print(f"queue {QUEUE} OK (DLX={DLX})")

try:
    ch.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=ROUTING_KEY)
    print(f"binding {QUEUE} <- {EXCHANGE} rk={ROUTING_KEY}")
except Exception as e:
    print(f"WARNING: binding principal fallo: {e}")

try:
    ch.queue_bind(queue=DLQ, exchange=DLX, routing_key="#")
    print(f"binding {DLQ} <- {DLX} rk=#")
except Exception as e:
    print(f"WARNING: binding DLQ fallo: {e}")

conn.close()
print("Topología verificada/creada.")