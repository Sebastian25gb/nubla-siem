import json
import logging
import os
import sys
from typing import Any, Dict, Optional

from jsonschema import Draft7Validator

from backend.app.core.config import settings
from backend.app.repository.elastic import get_es, index_event
from backend.app.processing.utils import prepare_event, top_validation_errors
from backend.app.infrastructure.rabbitmq import get_channel

logger = logging.getLogger(__name__)

try:
    from backend.app.processing.normalizer import normalize  # type: ignore
except Exception:
    def normalize(x: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore
        return x


def load_local_schema(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_validator(registry_url: Optional[str], subject: str, local_path: str) -> Optional[Draft7Validator]:
    # Intentar ruta absoluta real si la relativa falla
    resolved = local_path
    if not os.path.isabs(resolved):
        # Construir ruta relativa al paquete (consumer.py está en backend/app/processing)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "schema"))
        candidate = os.path.join(base_dir, os.path.basename(local_path))
        if os.path.exists(candidate):
            resolved = candidate
    try:
        schema = load_local_schema(resolved)
        logger.info("schema_loaded_local", extra={"path": resolved})
        return Draft7Validator(schema)
    except Exception:
        logger.warning("schema_validator_unavailable; continuing_without_validation", extra={"path": resolved}, exc_info=True)
        return None


def main() -> None:
    es = get_es()

    SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", getattr(settings, "schema_registry_url", None))
    NCS_SUBJECT = os.getenv("NCS_SUBJECT", "ncs-value")

    # Prioridad: env var > settings > fallback
    NCS_SCHEMA_LOCAL_PATH = os.getenv("NCS_SCHEMA_LOCAL_PATH", getattr(settings, "ncs_schema_local_path", "backend/app/schema/ncs_schema_registry.json"))
    validator = build_validator(SCHEMA_REGISTRY_URL, NCS_SUBJECT, NCS_SCHEMA_LOCAL_PATH)

    # RabbitMQ host override
    rmq_host = os.getenv("RABBITMQ_HOST", settings.rabbitmq_host)
    if rmq_host in ("rabbitmq", "localhost"):
        logger.info("rabbitmq_host_used", extra={"host": rmq_host})

    try:
        connection, channel, queue_name, exchange = get_channel()
    except Exception:
        logger.exception("rabbitmq_connection_failed")
        return

    def handle(ch, method, properties, body):
        try:
            raw_msg = json.loads(body)
            normalized = normalize(raw_msg)

            if hasattr(normalized, "model_dump"):
                evt_dict = normalized.model_dump()
            elif isinstance(normalized, dict):
                evt_dict = dict(normalized)
            else:
                evt_dict = json.loads(json.dumps(normalized, default=str))

            evt_dict = prepare_event(evt_dict)

            if validator is not None:
                errors = list(validator.iter_errors(evt_dict))
                if errors:
                    logger.warning(
                        "validation_failed",
                        extra={
                            "tenant_id": evt_dict.get("tenant_id"),
                            "errors": top_validation_errors(errors),
                        },
                    )
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    rk = getattr(method, "routing_key", None)
                    logger.info("nacked_to_dlx", extra={"routing_key": rk})
                    return

            tenant = evt_dict.get("tenant_id", "default")
            index_event(es, index=f"logs-{tenant}", body=evt_dict, pipeline="logs_ingest", ensure_required=False)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("event_indexed", extra={"tenant_id": tenant})
        except Exception:
            logger.exception("processing_failed")
            try:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            except Exception:
                pass
            rk = getattr(method, "routing_key", None)
            logger.info("nacked_to_dlx", extra={"routing_key": rk})

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=handle, auto_ack=False)
    logger.info("consumer_started", extra={"queue": queue_name, "exchange": exchange})
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
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(message)s",
        stream=sys.stdout,
    )
    main()