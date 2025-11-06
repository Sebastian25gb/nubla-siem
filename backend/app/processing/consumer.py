import json
import logging
import signal
from typing import Any

from core.logging import configure_logging
from core.config import settings
from infrastructure.rabbitmq import get_channel
from repository.elastic import get_es, index_event
from processing.normalizer import normalize

configure_logging()  # habilita logs INFO/JSON en stdout
logger = logging.getLogger(__name__)

_running = True
def _stop(*_: Any):
    global _running
    _running = False

signal.signal(signal.SIGINT, _stop)
signal.signal(signal.SIGTERM, _stop)

def main():
    es = get_es()
    conn, ch = get_channel()

    def handle(ch, method, properties, body):
        try:
            raw = json.loads(body)
            evt = normalize(raw)
            index_event(es, index=f"logs-{evt.tenant_id}", body=evt.model_dump())
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("event_indexed", extra={"tenant_id": evt.tenant_id})
        except Exception:
            logger.exception("processing_failed")
            # Evitar loops: mandar a DLX (nack sin requeue)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            try:
                rk = getattr(method, "routing_key", None)
            except Exception:
                rk = None
            logger.info("nacked_to_dlx", extra={"routing_key": rk})

    ch.basic_consume(queue=settings.rabbitmq_queue, on_message_callback=handle, auto_ack=False)
    logger.info("consumer_started")

    try:
        while _running:
            ch.connection.process_data_events(time_limit=1)
    finally:
        try:
            ch.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        logger.info("consumer_stopped")

if __name__ == "__main__":
    main()