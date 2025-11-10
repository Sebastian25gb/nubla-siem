#!/usr/bin/env python3
# Publica mensajes de prueba a RabbitMQ (usa la cola configurada en .env/.env.example)
import json
import os
import pika
from time import sleep

RABBIT_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBIT_USER = os.getenv("RABBITMQ_USER", "admin")
RABBIT_PASS = os.getenv("RABBITMQ_PASSWORD", "securepass")
QUEUE = os.getenv("RABBITMQ_QUEUE", "nubla_logs_default")
DLX = os.getenv("RABBITMQ_DLX", "logs_siem.dlx")  # asegurar que declaramos la misma DLX que el broker

credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
params = pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials)

def publish(body):
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    # Declarar la cola con el argumento x-dead-letter-exchange para que coincida con la cola ya existente
    args = {"x-dead-letter-exchange": DLX}
    ch.queue_declare(queue=QUEUE, durable=True, arguments=args)
    ch.basic_publish(exchange="", routing_key=QUEUE, body=json.dumps(body))
    conn.close()

# Mensaje válido (con campos obligatorios del NCS v1)
valid = {
  "tenant_id": "default",
  "@timestamp": "2025-11-10T18:00:00Z",
  "dataset": "syslog.generic",
  "schema_version": "1.0.0",
  "message": "valid event",
  "severity": "info",
  "source": {"ip": "127.0.0.1"}
}

# Mensaje inválido (falta tenant_id y otros)
invalid = {
  "@timestamp": "2025-11-10T18:00:00Z",
  "dataset": "syslog.generic",
  "message": "invalid event"
}

if __name__ == "__main__":
    print("Publishing valid event...")
    publish(valid)
    sleep(1)
    print("Publishing invalid event...")
    publish(invalid)
    print("Done.")