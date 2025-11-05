import pika
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from core.config import settings

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=10))
def _connect():
    creds = pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password)
    params = pika.ConnectionParameters(host=settings.rabbitmq_host, credentials=creds)
    return pika.BlockingConnection(params)

def declare_topology(channel: pika.adapters.blocking_connection.BlockingChannel):
    # Exchange principal (no durable para evitar choque con plugin de Fluentd)
    channel.exchange_declare(
        exchange=settings.rabbitmq_exchange,
        exchange_type="topic",
        durable=False
    )

    # Dead-letter exchange (no durable por compatibilidad)
    dlx = f"{settings.rabbitmq_exchange}.dlx"
    channel.exchange_declare(
        exchange=dlx,
        exchange_type="fanout",
        durable=False
    )

    # Cola principal (durable) con DLX
    args = {"x-dead-letter-exchange": dlx}
    channel.queue_declare(
        queue=settings.rabbitmq_queue,
        durable=True,
        arguments=args
    )
    channel.queue_bind(
        queue=settings.rabbitmq_queue,
        exchange=settings.rabbitmq_exchange,
        routing_key=settings.rabbitmq_routing_key
    )

    # DLQ visible para inspección de errores
    dlq_queue = f"{settings.rabbitmq_exchange}.dlq"
    channel.queue_declare(
        queue=dlq_queue,
        durable=True
    )
    # Fanout: routing key ignorada
    channel.queue_bind(
        queue=dlq_queue,
        exchange=dlx
    )

def get_channel():
    conn = _connect()
    ch = conn.channel()
    declare_topology(ch)
    ch.basic_qos(prefetch_count=50)
    return conn, ch