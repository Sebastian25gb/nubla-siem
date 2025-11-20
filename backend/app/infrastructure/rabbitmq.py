import logging
import os

import pika
from pika.exceptions import ChannelClosedByBroker

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def _ensure_exchange(
    channel: pika.channel.Channel, exchange: str, exchange_type: str = "topic", durable: bool = True
) -> pika.channel.Channel:
    try:
        channel.exchange_declare(exchange=exchange, passive=True)
        return channel
    except ChannelClosedByBroker:
        logger.info("exchange_not_found_creating", extra={"exchange": exchange})
        conn = channel.connection
        new_ch = conn.channel()
        new_ch.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=durable)
        return new_ch


def _ensure_queue(
    channel: pika.channel.Channel, queue: str, arguments: dict
) -> pika.channel.Channel:
    try:
        channel.queue_declare(queue=queue, passive=True)
        return channel
    except ChannelClosedByBroker:
        logger.info("queue_not_found_creating", extra={"queue": queue, "arguments": arguments})
        conn = channel.connection
        new_ch = conn.channel()
        new_ch.queue_declare(queue=queue, durable=True, arguments=arguments)
        return new_ch


def declare_topology(channel: pika.channel.Channel) -> tuple[pika.channel.Channel, str, str]:
    exchange = getattr(
        settings, "rabbitmq_exchange", os.getenv("RABBITMQ_EXCHANGE", "logs_default")
    )
    queue = getattr(settings, "rabbitmq_queue", os.getenv("RABBITMQ_QUEUE", "nubla_logs_default"))
    dlx = getattr(settings, "rabbitmq_dlx", os.getenv("RABBITMQ_DLX", "logs_default.dlx"))
    routing_key = getattr(
        settings, "rabbitmq_routing_key", os.getenv("RABBITMQ_ROUTING_KEY", "nubla.log.default")
    )

    channel = _ensure_exchange(channel, exchange, exchange_type="topic", durable=True)
    channel = _ensure_exchange(channel, dlx, exchange_type="topic", durable=True)

    args = {"x-dead-letter-exchange": dlx}
    channel = _ensure_queue(channel, queue, arguments=args)

    channel.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)
    return channel, queue, exchange


def get_channel():
    host = getattr(settings, "rabbitmq_host", os.getenv("RABBITMQ_HOST", "rabbitmq"))
    user = getattr(settings, "rabbitmq_user", os.getenv("RABBITMQ_USER", "admin"))
    password = getattr(settings, "rabbitmq_password", os.getenv("RABBITMQ_PASSWORD", "securepass"))
    virtual_host = getattr(settings, "rabbitmq_vhost", os.getenv("RABBITMQ_VHOST", "/"))
    port = int(getattr(settings, "rabbitmq_port", os.getenv("RABBITMQ_PORT", 5672)))

    credentials = pika.PlainCredentials(user, password)
    params = pika.ConnectionParameters(
        host=host, port=port, virtual_host=virtual_host, credentials=credentials
    )

    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch, queue, exchange = declare_topology(ch)
    return conn, ch, queue, exchange
