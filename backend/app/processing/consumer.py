import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict

import pika
from jsonschema import Draft7Validator

from core.config import settings
from repository.elastic import get_es, index_event

logger = logging.getLogger(__name__)

try:
    from processing.normalizer import normalize  # type: ignore
except Exception:
    def normalize(x: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore
        return x

def to_iso8601(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return value

def coerce_datetimes(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: coerce_datetimes(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [coerce_datetimes(v) for v in obj]
    return to_iso8601(obj)

def load_local_schema(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        logger.info("schema_loaded_local", extra={"path": path})
        return schema
    except Exception:
        logger.error("load_local_schema_failed", exc_info=True, extra={"path": path})
        raise

def build_validator(registry_url: str | None, subject: str, local_path: str) -> Draft7Validator | None:
    try:
        schema = load_local_schema(local_path)
        return Draft7Validator(schema)
    except Exception:
        logger.warning("schema_validator_unavailable; continuing_without_validation")
        return None

def main() -> None:
    es = get_es()

    SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", getattr(settings, "schema_registry_url", None))
    NCS_SUBJECT = os.getenv("NCS_SUBJECT", "ncs-value")
    NCS_SCHEMA_LOCAL_PATH = os.getenv("NCS_SCHEMA_LOCAL_PATH", "schema/ncs_schema_registry.json")

    validator = build_validator(SCHEMA_REGISTRY_URL, NCS_SUBJECT, NCS_SCHEMA_LOCAL_PATH)

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

            if "@timestamp" not in evt_dict:
                if "timestamp" in evt_dict:
                    evt_dict["@timestamp"] = evt_dict["timestamp"]
                else:
                    evt_dict["@timestamp"] = datetime.now(timezone.utc).isoformat()
            evt_dict = coerce_datetimes(evt_dict)
            if "dataset" not in evt_dict:
                evt_dict["dataset"] = "syslog.generic"
            if "schema_version" not in evt_dict:
                evt_dict["schema_version"] = "1.0.0"

            if validator is not None:
                errors = list(validator.iter_errors(evt_dict))
                if errors:
                    err_messages = [f"{e.message} (path: {list(e.path)})" for e in errors[:5]]
                    logger.warning("validation_failed", extra={"tenant_id": evt_dict.get("tenant_id"), "errors": err_messages})
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    rk = getattr(method, "routing_key", None)
                    logger.info("nacked_to_dlx", extra={"routing_key": rk})
                    return

            tenant = evt_dict.get("tenant_id", "unknown")
            index_event(es, index=f"logs-{tenant}", body=evt_dict, pipeline="logs_ingest")
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