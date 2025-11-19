import pika, json, os

RABBIT_USER = os.environ.get("RABBIT_USER", "admin")
RABBIT_PASS = os.environ.get("RABBIT_PASS", "securepass")
RABBIT_HOST = os.environ.get("RABBIT_HOST", "127.0.0.1")
RABBIT_PORT = int(os.environ.get("RABBIT_PORT", "5672"))

creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
params = pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT, credentials=creds)
conn = pika.BlockingConnection(params)
ch = conn.channel()
ch.exchange_declare(exchange='app.events', exchange_type='topic', durable=True)

message = {
    "tenant_id": "single-tenant",
    "event_id": "test-1",
    "timestamp": "2025-11-19T21:00:00Z",
    "source": "test-producer",
    "event_type": "log",
    "metadata": {"host": "devbox"},
    "payload": {"message": "mensaje de prueba"}
}

ch.basic_publish(
    exchange='app.events',
    routing_key='tenant.single-tenant.log',
    body=json.dumps(message),
    properties=pika.BasicProperties(content_type='application/json', delivery_mode=2)
)
print("published")
conn.close()