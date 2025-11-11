import json
import logging
import os
import sys
from typing import Any, Dict

import pika
from jsonschema import Draft7Validator

from core.config import settings
from repository.elastic import get_es, index_event
from processing.utils import prepare_event, top_validation_errors  # new helpers

logger = logging.getLogger(__name__)

# Intentar importar el normalizador; si no existe, usar passthrough
try:
    from processing.normalizer import normalize  # type: ignore
except Exception:
    def normalize(x: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore
        return x

def load_local_schema(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_validator(registry_url: str | None, subject: str, local_path: str) -> Draft7Validator | None:
    # Por ahora usamos siempre el schema local como fallback
    try:
        schema = load_local_schema(local_path)
        logger.info("schema_loaded_local", extra={"path": local_path})
        return Draft7Validator(schema)
    except Exception:
        logger.warning("schema_validator_unavailable; continuing_without_validation", exc_info=True)
        return None

def main() -> None:
    # OpenSearch/Elasticsearch client
    es = get_es()

    # Schema config
    SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", getattr(settings, "schema_registry_url", None))
    NCS_SUBJECT = os.getenv("NCS_SUBJECT", "ncs-value")
    NCS_SCHEMA_LOCAL_PATH = os.getenv("NCS_SCHEMA_LOCAL_PATH", "schema/ncs_schema_registry.json")
    validator = build_validator(SCHEMA_REGISTRY_URL, NCS_SUBJECT, NCS_SCHEMA_LOCAL_PATH)

    # RabbitMQ connection
    rmq_host = getattr(settings, "rabbitmq_host", os.getenv("RABBITMQ_HOST", "rabbitmq"))
    rmq_user = getattr(settings, "rabbitmq_user", os.getenv("RABBITMQ_USER", "admin"))
    rmq_pass = getattr(settings, "rabbitmq_password", os.getenv("RABBITMQ_PASSWORD", "securepass"))
    rmq_vhost = getattr(settings, "rabbitmq_vhost", os.getenv("RABBITMQ_VHOST", "/"))
    queue_name = getattr(settings, "rabbitmq_queue", os.getenv("RABBITMQ_QUEUE", "nubla_logs_default"))

    credentials = pika.PlainCredentials(rmq_user, rmq_pass)
    params = pika.ConnectionParameters(host=rmq_host, virtual_host=rmq_vhost, credentials=credentials)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

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

            # Completar mínimos
            evt_dict = prepare_event(evt_dict)

            # Validación
            if validator is not None:
                errors = list(validator.iter_errors(evt_dict))
                if errors:
                    logger.warning("validation_failed", extra={"tenant_id": evt_dict.get("tenant_id"), "errors": top_validation_errors(errors)})
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    rk = getattr(method, "routing_key", None)
                    logger.info("nacked_to_dlx", extra={"routing_key": rk})
                    return

            # Indexar con pipeline enriquecido
            tenant = evt_dict.get("tenant_id", "unknown")
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
    logger.info("consumer_started")
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