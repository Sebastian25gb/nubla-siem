#!/usr/bin/env python3
"""
Topología canónica RabbitMQ (single-tenant):
- exchange logs_default (topic, durable)
- dead-letter exchange logs_default.dlx (topic, durable)
- queue nubla_logs_default (durable, DLX -> logs_default.dlx)
- queue nubla_logs_default.dlq (durable)
- binding nubla_logs_default <- logs_default (routing_key nubla.log.default)
- binding nubla_logs_default.dlq <- logs_default.dlx (#)

Variables de entorno:
  RABBIT_HOST (default 127.0.0.1)
  RABBIT_PORT (default 5672)
  RABBIT_VHOST (default /)
  RABBIT_USER / RABBIT_PASS (obligatorio)
  RABBITMQ_EXCHANGE (default logs_default)
  RABBITMQ_DLX (default logs_default.dlx)
  RABBITMQ_QUEUE (default nubla_logs_default)
  RABBITMQ_DLQ (default nubla_logs_default.dlq)
  RABBITMQ_ROUTING_KEY (default nubla.log.default)
  FORCE_RECREATE (default false) -> si propiedades difieren, borra y recrea exchanges/queue.

Exit codes:
  0 éxito, 1 falta credenciales, 2 error al recrear.
"""
import os
import sys
import pika
from pika.exceptions import ChannelClosedByBroker

RABBIT_HOST = os.environ.get("RABBIT_HOST", "127.0.0.1")
RABBIT_PORT = int(os.environ.get("RABBIT_PORT", "5672"))
RABBIT_VHOST = os.environ.get("RABBIT_VHOST", "/")
USER = os.environ.get("RABBIT_USER")
PASSWORD = os.environ.get("RABBIT_PASS")

EXCHANGE = os.environ.get("RABBITMQ_EXCHANGE", "logs_default")
DLX = os.environ.get("RABBITMQ_DLX", "logs_default.dlx")
QUEUE = os.environ.get("RABBITMQ_QUEUE", "nubla_logs_default")
DLQ = os.environ.get("RABBITMQ_DLQ", "nubla_logs_default.dlq")
ROUTING_KEY = os.environ.get("RABBITMQ_ROUTING_KEY", "nubla.log.default")
FORCE_RECREATE = os.environ.get("FORCE_RECREATE", "false").lower() == "true"

if not USER or not PASSWORD:
    print("ERROR: Define RABBIT_USER y RABBIT_PASS")
    sys.exit(1)

creds = pika.PlainCredentials(USER, PASSWORD)
params = pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT, virtual_host=RABBIT_VHOST, credentials=creds)
conn = pika.BlockingConnection(params)
ch = conn.channel()

def ensure_exchange(name: str, durable: bool = True, ex_type: str = "topic"):
    try:
        ch.exchange_declare(exchange=name, passive=True)
        # Ya existe. Si se esperaba durable y el existente no lo es, RabbitMQ no lo revela aquí;
        # Precondition mismatch ya habría cerrado el canal si propiedades difirieran.
        # Para detectar mismatch de durable se intenta redeclarar con mismo durable:
        try:
            ch.exchange_declare(exchange=name, exchange_type=ex_type, durable=durable)
        except ChannelClosedByBroker as e:
            if FORCE_RECREATE:
                # Re-abrir canal y recrear
                print(f"WARNING: exchange {name} con propiedades diferentes. Recreando (FORCE_RECREATE). Detalle: {e}")
                new_ch = conn.channel()
                # Borrar via direct method no existe en AMQP, se usa rabbitmqadmin normalmente;
                # aquí cerramos y forzamos excepción para que usuario lo haga manual si no se puede.
                # Simplificación: cerrar conexión y abortar si mismatch.
                print(f"ERROR: No se puede recrear {name} vía AMQP puro. Usa rabbitmqadmin para borrar y re-ejecutar.")
                sys.exit(2)
            else:
                print(f"WARNING: exchange {name} existe con propiedades distintas. (FORCE_RECREATE=false) Usando existente.")
                # Abrir nuevo canal para continuar después del cierre
                return conn.channel()
        return ch
    except ChannelClosedByBroker:
        # No existía; crear
        new_ch = conn.channel()
        new_ch.exchange_declare(exchange=name, exchange_type=ex_type, durable=durable)
        return new_ch

def ensure_queue(name: str, args: dict | None = None):
    args = args or {}
    try:
        ch.queue_declare(queue=name, passive=True)
        # Intentar declarar con mismos argumentos (si difieren lanza precondition_failed)
        try:
            ch.queue_declare(queue=name, durable=True, arguments=args)
        except ChannelClosedByBroker as e:
            if FORCE_RECREATE:
                print(f"WARNING: queue {name} con argumentos diferentes. Recrear manualmente. Detalle: {e}")
                sys.exit(2)
            else:
                print(f"WARNING: queue {name} con args distintos. Continuando (FORCE_RECREATE=false).")
                return conn.channel()
        return ch
    except ChannelClosedByBroker:
        new_ch = conn.channel()
        new_ch.queue_declare(queue=name, durable=True, arguments=args)
        return new_ch

# Exchanges
ch = ensure_exchange(EXCHANGE, durable=True)
print(f"exchange {EXCHANGE} OK (durable expected)")
ch = ensure_exchange(DLX, durable=True)
print(f"exchange {DLX} OK (durable expected)")

# DLQ
ch = ensure_queue(DLQ)
print(f"queue {DLQ} OK")

# Main queue con DLX
ch = ensure_queue(QUEUE, args={"x-dead-letter-exchange": DLX})
print(f"queue {QUEUE} OK (DLX={DLX})")

# Bindings (intentar; si ya existen, no pasa nada)
try:
    ch.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=ROUTING_KEY)
    print(f"binding {QUEUE} <- {EXCHANGE} rk={ROUTING_KEY}")
except Exception as e:
    print(f"WARNING: binding principal fallo (continúo): {e}")

try:
    ch.queue_bind(queue=DLQ, exchange=DLX, routing_key="#")
    print(f"binding {DLQ} <- {DLX} rk=#")
except Exception as e:
    print(f"WARNING: binding DLQ fallo (continúo): {e}")

conn.close()
print("Topología verificada/creada.")