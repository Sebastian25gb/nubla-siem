#!/usr/bin/env python3
import pika, json, os, time, sys

RABBIT_USER = os.environ.get("RABBIT_USER", "admin")
RABBIT_PASS = os.environ.get("RABBIT_PASS", "securepass")
RABBIT_HOST = os.environ.get("RABBIT_HOST", "127.0.0.1")
RABBIT_PORT = int(os.environ.get("RABBIT_PORT", "5672"))

creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
params = pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT, credentials=creds)

try:
    conn = pika.BlockingConnection(params)
except Exception as e:
    print("ERROR: no se pudo conectar a RabbitMQ:", e)
    sys.exit(1)

ch = conn.channel()

# Declarar la cola con el mismo argumento DLX que usamos al crear la topología
dlx_args = {"x-dead-letter-exchange": "app.dlx"}
ch.queue_declare(queue='app.processing', durable=True, arguments=dlx_args)

ch.basic_qos(prefetch_count=10)

def callback(ch, method, properties, body):
    msg = json.loads(body)
    try:
        print("RECIBIDO:", msg.get('tenant_id'), msg.get('payload', {}).get('message'))
        # Simula trabajo
        time.sleep(0.5)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print("Error procesando mensaje:", e)
        # No reencolamos para evitar loops infinitos; enviar a DLQ
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

ch.basic_consume('app.processing', callback)
print("Esperando mensajes...")
ch.start_consuming()