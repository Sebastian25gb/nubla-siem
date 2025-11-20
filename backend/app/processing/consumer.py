import json
import logging
import os
from typing import Any, Dict, Optional

from jsonschema import Draft7Validator
from prometheus_client import Counter, start_http_server

from backend.app.core.config import settings
from backend.app.core.logging import configure_logging
from backend.app.infrastructure.rabbitmq import get_channel
from backend.app.processing.normalizer import normalize
from backend.app.processing.utils import prepare_event, top_validation_errors
from backend.app.repository.elastic import get_es, index_event

logger = logging.getLogger(__name__)

EVENTS_PROCESSED = Counter("events_processed_total", "Total events consumed")
EVENTS_INDEXED = Counter("events_indexed_total", "Events successfully indexed")
EVENTS_NACKED = Counter("events_nacked_total", "Events sent to DLX/DLQ")
EVENTS_VALIDATION_FAILED = Counter("events_validation_failed_total", "Schema validation failures")
EVENTS_INDEX_FAILED = Counter("events_index_failed_total", "Index operation failures")

USE_MANUAL_DLX = os.getenv("USE_MANUAL_DLX", "false").lower() == "true"
MANUAL_DLX_EXCHANGE = os.getenv("RABBITMQ_DLX", "logs_default.dlx")


def load_local_schema(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_validator(local_path: str) -> Optional[Draft7Validator]:
    resolved = local_path
    if not os.path.isabs(resolved):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "schema"))
        candidate = os.path.join(base_dir, os.path.basename(local_path))
        if os.path.exists(candidate):
            resolved = candidate
    try:
        schema = load_local_schema(resolved)
        logger.info("schema_loaded_local", extra={"path": resolved})
        return Draft7Validator(schema)
    except Exception:
        logger.warning("schema_validator_unavailable", extra={"path": resolved}, exc_info=True)
        return None


def publish_to_dlx_with_reason(ch, body_bytes: bytes, routing_key: str, reason: str):
    try:
        import pika

        props = pika.BasicProperties(headers={"x-reject-reason": reason})
    except Exception:
        props = None
    ch.basic_publish(
        exchange=MANUAL_DLX_EXCHANGE, routing_key=routing_key, body=body_bytes, properties=props
    )
    EVENTS_NACKED.inc()


def main() -> None:
    try:
        start_http_server(int(os.getenv("METRICS_PORT", "9109")))
        logger.info("metrics_server_started", extra={"port": os.getenv("METRICS_PORT", "9109")})
    except Exception:
        logger.warning("metrics_server_failed", exc_info=True)

    es = get_es()

    schema_path = os.getenv(
        "NCS_SCHEMA_LOCAL_PATH",
        getattr(settings, "ncs_schema_local_path", "backend/app/schema/ncs_v1.0.0.json"),
    )
    validator = build_validator(schema_path)

    try:
        connection, channel, queue_name, exchange = get_channel()
    except Exception:
        logger.exception("rabbitmq_connection_failed")
        return

    def handle(ch, method, properties, body):
        EVENTS_PROCESSED.inc()
        try:
            raw_msg = json.loads(body)
            normalized = normalize(raw_msg)
            if isinstance(normalized, dict):
                evt_dict = dict(normalized)
            else:
                evt_dict = json.loads(json.dumps(normalized, default=str))

            # Lowercase severity antes de validar (si existe)
            if "severity" in evt_dict and isinstance(evt_dict["severity"], str):
                evt_dict["severity"] = evt_dict["severity"].lower()

            evt_dict = prepare_event(evt_dict)

            if validator is not None:
                errors = list(validator.iter_errors(evt_dict))
                if errors:
                    EVENTS_VALIDATION_FAILED.inc()
                    logger.warning(
                        "validation_failed",
                        extra={
                            "tenant_id": evt_dict.get("tenant_id"),
                            "errors": top_validation_errors(errors),
                        },
                    )
                    if USE_MANUAL_DLX:
                        publish_to_dlx_with_reason(
                            ch, body, method.routing_key, "validation_failed"
                        )
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                        EVENTS_NACKED.inc()
                    return

            tenant = evt_dict.get("tenant_id", "default")
            try:
                index_event(
                    es,
                    index=f"logs-{tenant}",
                    body=evt_dict,
                    pipeline="logs_ingest",
                    ensure_required=False,
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                EVENTS_INDEXED.inc()
                logger.info("event_indexed", extra={"tenant_id": tenant})
            except Exception:
                EVENTS_INDEX_FAILED.inc()
                logger.exception("index_failed")
                if USE_MANUAL_DLX:
                    publish_to_dlx_with_reason(ch, body, method.routing_key, "index_failed")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    EVENTS_NACKED.inc()
        except Exception:
            logger.exception("processing_failed")
            if USE_MANUAL_DLX:
                publish_to_dlx_with_reason(
                    ch, body, getattr(method, "routing_key", "unknown"), "processing_exception"
                )
                try:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception:
                    pass
            else:
                try:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    EVENTS_NACKED.inc()
                except Exception:
                    pass

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=handle, auto_ack=False)
    logger.info(
        "consumer_started",
        extra={"queue": queue_name, "exchange": exchange, "manual_dlx": USE_MANUAL_DLX},
    )
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        try:
            connection.close()
        except Exception:
            pass


if __name__ == "__main__":
    configure_logging(level=os.getenv("LOG_LEVEL", "INFO"))
    main()
