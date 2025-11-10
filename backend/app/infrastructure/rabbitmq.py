import os
import logging
import pika

from core.config import settings

logger = logging.getLogger(__name__)


def declare_topology(channel: pika.channel.Channel) -> None:
    """
    Declare exchanges/queues used by the app. Use env/settings for DLX name to match existing broker config.
    Declares:
      - main exchange (from settings.rabbitmq_exchange)
      - dead-letter exchange (from RABBITMQ_DLX or settings.rabbitmq_dlx)
      - queue (settings.rabbitmq_queue) with x-dead-letter-exchange pointing to the DLX
    """
    exchange = getattr(settings, "rabbitmq_exchange", os.getenv("RABBITMQ_EXCHANGE", "logs_default"))
    queue = getattr(settings, "rabbitmq_queue", os.getenv("RABBITMQ_QUEUE", "nubla_logs_default"))

    # Allow overriding DLX via settings or env; default to the DLX observed in the broker
    dlx = getattr(settings, "rabbitmq_dlx", os.getenv("RABBITMQ_DLX", "logs_siem.dlx"))

    # Ensure exchanges exist (durable)
    try:
        # Main exchange (topic/direct as appropriate). Use 'topic' for flexibility.
        channel.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
    except Exception:
        logger.exception("exchange_declare_failed", extra={"exchange": exchange})
        raise

    try:
        # Dead-letter exchange (durable)
        channel.exchange_declare(exchange=dlx, exchange_type="topic", durable=True)
    except Exception:
        logger.exception("dlx_declare_failed", extra={"dlx": dlx})
        raise

    # Queue arguments: set DLX to match the broker
    args = {"x-dead-letter-exchange": dlx}

    try:
        # Declare the queue with the DLX argument (idempotent if args match)
        channel.queue_declare(queue=queue, durable=True, arguments=args)
    except Exception:
        logger.exception("queue_declare_failed", extra={"queue": queue, "arguments": args})
        raise

    # Bind queue to exchange with a generic routing key (if your topology uses routing keys, adapt accordingly)
    try:
        # Use a sensible default binding so messages published to the exchange reach the queue.
        # If your producers publish with specific routing keys, adjust/bind accordingly.
        channel.queue_bind(queue=queue, exchange=exchange, routing_key="#")
    except Exception:
        logger.exception("queue_bind_failed", extra={"queue": queue, "exchange": exchange})
        raise


def get_channel():
    """
    Create a connection and return (connection, channel).
    Connection parameters are read from settings or env vars.
    """
    host = getattr(settings, "rabbitmq_host", os.getenv("RABBITMQ_HOST", "rabbitmq"))
    user = getattr(settings, "rabbitmq_user", os.getenv("RABBITMQ_USER", "admin"))
    password = getattr(settings, "rabbitmq_password", os.getenv("RABBITMQ_PASSWORD", "securepass"))
    virtual_host = getattr(settings, "rabbitmq_vhost", os.getenv("RABBITMQ_VHOST", "/"))
    port = int(getattr(settings, "rabbitmq_port", os.getenv("RABBITMQ_PORT", 5672)))

    credentials = pika.PlainCredentials(user, password)
    params = pika.ConnectionParameters(host=host, port=port, virtual_host=virtual_host, credentials=credentials)

    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Declare topology idempotently
    declare_topology(ch)

    return conn, ch