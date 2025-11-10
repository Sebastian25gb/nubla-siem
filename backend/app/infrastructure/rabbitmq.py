import os
import logging
import pika
from pika.exceptions import ChannelClosedByBroker

from core.config import settings

logger = logging.getLogger(__name__)


def _ensure_exchange(channel: pika.channel.Channel, exchange: str, exchange_type: str = "topic", durable: bool = True) -> pika.channel.Channel:
    """
    Ensure an exchange exists. If it already exists, a passive declare will succeed (no-op).
    If it doesn't exist the passive declare will close the channel; in that case create a fresh
    channel and declare the exchange with the desired properties.
    Returns a channel that is open and ready for further operations.
    """
    try:
        # passive=True checks existence without modifying properties
        channel.exchange_declare(exchange=exchange, passive=True)
        return channel
    except ChannelClosedByBroker:
        # channel closed because exchange doesn't exist; create a new channel and declare it
        logger.info("exchange_not_found_creating", extra={"exchange": exchange})
        conn = channel.connection
        new_ch = conn.channel()
        new_ch.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=durable)
        return new_ch


def _ensure_queue(channel: pika.channel.Channel, queue: str, arguments: dict) -> pika.channel.Channel:
    """
    Ensure a queue exists. If it already exists, a passive declare will succeed (no-op).
    If it doesn't exist the passive declare will close the channel; in that case create a fresh
    channel and declare the queue with the desired arguments.
    Returns a channel that is open and ready for further operations.
    """
    try:
        channel.queue_declare(queue=queue, passive=True)
        return channel
    except ChannelClosedByBroker:
        logger.info("queue_not_found_creating", extra={"queue": queue, "arguments": arguments})
        conn = channel.connection
        new_ch = conn.channel()
        new_ch.queue_declare(queue=queue, durable=True, arguments=arguments)
        return new_ch


def declare_topology(channel: pika.channel.Channel) -> pika.channel.Channel:
    """
    Declare exchanges/queues used by the app in an idempotent and safe way.
    Returns the (possibly new) open channel to use afterwards.
    """
    exchange = getattr(settings, "rabbitmq_exchange", os.getenv("RABBITMQ_EXCHANGE", "logs_default"))
    queue = getattr(settings, "rabbitmq_queue", os.getenv("RABBITMQ_QUEUE", "nubla_logs_default"))

    # Allow overriding DLX via settings or env; default to the DLX observed in the broker
    dlx = getattr(settings, "rabbitmq_dlx", os.getenv("RABBITMQ_DLX", "logs_siem.dlx"))

    # Exchange: ensure exists (if not, create with durable=True)
    channel = _ensure_exchange(channel, exchange, exchange_type="topic", durable=True)

    # Dead-letter exchange: ensure exists (create if missing)
    channel = _ensure_exchange(channel, dlx, exchange_type="topic", durable=True)

    # Queue arguments: set DLX to match broker / config
    args = {"x-dead-letter-exchange": dlx}

    # Queue: ensure exists (if not, create with args)
    channel = _ensure_queue(channel, queue, arguments=args)

    # Bind the queue to the exchange (best-effort). If binding fails it will raise.
    try:
        channel.queue_bind(queue=queue, exchange=exchange, routing_key="#")
    except Exception:
        logger.exception("queue_bind_failed", extra={"queue": queue, "exchange": exchange})
        raise

    return channel


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

    # Declare topology idempotently and get back an open channel
    ch = declare_topology(ch)

    return conn, ch