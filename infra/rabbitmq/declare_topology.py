#!/usr/bin/env python3
"""
Declara topología RabbitMQ:
- exchange topic app.events (durable)
- exchange topic app.dlx (durable)
- queue app.dlq (durable)
- queue app.processing (durable) con x-dead-letter-exchange -> app.dlx
- binding app.processing <- app.events routing_key tenant.single-tenant.#
Uso: RABBIT_USER=admin RABBIT_PASS=... python3 infra/rabbitmq/declare_topology.py
"""
import os
import pika
import sys

RABBIT_HOST = os.environ.get("RABBIT_HOST", "127.0.0.1")
RABBIT_PORT = int(os.environ.get("RABBIT_PORT", "5672"))
USER = os.environ.get("RABBIT_USER")
PASSWORD = os.environ.get("RABBIT_PASS")

if not USER or not PASSWORD:
    print("Error: define RABBIT_USER y RABBIT_PASS como variables de entorno.")
    print("Ej: RABBIT_USER=admin RABBIT_PASS=TuPassSeguro python3 infra/rabbitmq/declare_topology.py")
    sys.exit(1)

creds = pika.PlainCredentials(USER, PASSWORD)
params = pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT, credentials=creds)
conn = pika.BlockingConnection(params)
ch = conn.channel()

# Exchanges
ch.exchange_declare(exchange="app.events", exchange_type="topic", durable=True)
print("exchange app.events creado (topic, durable)")
ch.exchange_declare(exchange="app.dlx", exchange_type="topic", durable=True)
print("exchange app.dlx creado (topic, durable)")

# DLQ
ch.queue_declare(queue="app.dlq", durable=True)
print("queue app.dlq creada (durable)")

# main processing queue con DLX
args = {"x-dead-letter-exchange": "app.dlx"}
ch.queue_declare(queue="app.processing", durable=True, arguments=args)
print("queue app.processing creada (durable) con DLX -> app.dlx")

# binding (single-tenant)
ch.queue_bind(queue="app.processing", exchange="app.events", routing_key="tenant.single-tenant.#")
print("binding app.processing <- app.events con routing_key 'tenant.single-tenant.#'")

# bind DLX->DLQ
ch.queue_bind(queue="app.dlq", exchange="app.dlx", routing_key="#")
print("binding app.dlq <- app.dlx (routing_key '#')")

conn.close()
print("Topología creada correctamente.")