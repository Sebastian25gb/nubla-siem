import json
import os
from datetime import datetime, timezone
import pika

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "securepass")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")
RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "logs_default")
RABBITMQ_ROUTING_KEY = os.getenv("RABBITMQ_ROUTING_KEY", "nubla.log.default")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "nubla_logs_default")

def publish(body: dict, use_exchange: bool = True):
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        virtual_host=RABBITMQ_VHOST,
    )
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    if use_exchange:
        ch.basic_publish(exchange=RABBITMQ_EXCHANGE, routing_key=RABBITMQ_ROUTING_KEY, body=json.dumps(body).encode("utf-8"))
    else:
        ch.basic_publish(exchange="", routing_key=RABBITMQ_QUEUE, body=json.dumps(body).encode("utf-8"))
    conn.close()

def main():
    print("Publishing valid event...")
    valid_event = {
        "tenant_id": "default",
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": "syslog.generic",
        "schema_version": "1.0.0",
        "severity": "info",
        "message": "valid event",
        "source": {"ip": "1.1.1.1"},
        "host": "demo-host"
    }
    publish(valid_event, use_exchange=True)

    print("Publishing invalid event...")
    invalid_event = {
        "tenant_id": "default",
        "message": "invalid event",
        "severity": None
    }
    publish(invalid_event, use_exchange=True)

    print("Done.")

if __name__ == "__main__":
    main()