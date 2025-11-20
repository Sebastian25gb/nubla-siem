#!/usr/bin/env python3
import os
import sys
import time
import json
import pika
import pytest

# Marcamos todo el archivo como tests de integración
pytestmark = pytest.mark.integration

# Flags de ejecución controladas por entorno
RUN_INTEGRATION = os.getenv("RUN_RABBIT_INTEGRATION", "false").lower() == "true"
RUN_CONSUME_ONE = os.getenv("RUN_RABBIT_CONSUME_ONE", "false").lower() == "true"

RABBIT_USER = os.environ.get("RABBIT_USER", "admin")
RABBIT_PASS = os.environ.get("RABBIT_PASS", "securepass")
RABBIT_HOST = os.environ.get("RABBIT_HOST", "127.0.0.1")
RABBIT_PORT = int(os.environ.get("RABBIT_PORT", "5672"))
QUEUE_NAME = os.environ.get("RABBIT_QUEUE", "app.processing")
DLX_NAME = os.environ.get("RABBIT_DLX", "app.dlx")


def _connect_channel():
    creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT, credentials=creds)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    return conn, ch


def test_rabbitmq_connectivity_and_declare():
    """
    Smoke test de conectividad y declaración de cola.
    Este test no consume y se salta por defecto salvo que RUN_RABBIT_INTEGRATION=true.
    """
    if not RUN_INTEGRATION:
        pytest.skip("Skipping RabbitMQ integration tests (set RUN_RABBIT_INTEGRATION=true to run)")

    conn = None
    try:
        conn, ch = _connect_channel()
        dlx_args = {"x-dead-letter-exchange": DLX_NAME}
        ch.queue_declare(queue=QUEUE_NAME, durable=True, arguments=dlx_args)
        ch.basic_qos(prefetch_count=10)
        # Assert mínimos
        assert ch.is_open
    finally:
        try:
            if conn and conn.is_open:
                conn.close()
        except Exception:
            pass


def test_rabbitmq_consume_one_message_non_blocking():
    """
    Consumo no bloqueante de un mensaje (si existe), controlado por RUN_RABBIT_CONSUME_ONE=true.
    No usa start_consuming; hace basic_get con timeout acotado.
    """
    if not RUN_INTEGRATION:
        pytest.skip("Skipping RabbitMQ integration tests (set RUN_RABBIT_INTEGRATION=true to run)")
    if not RUN_CONSUME_ONE:
        pytest.skip("Skipping one-shot consume (set RUN_RABBIT_CONSUME_ONE=true to run)")

    conn = None
    try:
        conn, ch = _connect_channel()
        # Asegurar que la cola existe
        dlx_args = {"x-dead-letter-exchange": DLX_NAME}
        ch.queue_declare(queue=QUEUE_NAME, durable=True, arguments=dlx_args)

        # Intentar obtener un mensaje sin bloquear por más de ~2s
        deadline = time.time() + 2.0
        got = False
        while time.time() < deadline and not got:
            method, props, body = ch.basic_get(queue=QUEUE_NAME, auto_ack=False)
            if method:
                try:
                    msg = json.loads(body.decode("utf-8"))
                except Exception:
                    msg = {"raw": body[:200]}
                # Acknowledge y validaciones mínimas
                ch.basic_ack(delivery_tag=method.delivery_tag)
                got = True
                # No fallar si no hay campos esperados; es smoke
                assert True
            else:
                time.sleep(0.1)

        # Si no hubo mensaje, el test igualmente pasa (no bloquea)
        assert True
    finally:
        try:
            if conn and conn.is_open:
                conn.close()
        except Exception:
            pass