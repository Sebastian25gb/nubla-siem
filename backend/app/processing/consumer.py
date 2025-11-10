import json
import logging
import os
import signal
from typing import Any, List, Optional

import requests
import jsonschema
from jsonschema import Draft7Validator

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


def fetch_schema_from_registry(schema_registry_url: str, subject: str) -> dict:
    """
    Fetch latest schema registered for a subject from a Confluent-compatible Schema Registry.
    Returns a JSON Schema (dict).
    """
    url = f"{schema_registry_url.rstrip('/')}/subjects/{subject}/versions/latest"
    logger.info("fetching_schema", extra={"url": url})
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    raw_schema = payload.get("schema")
    if raw_schema is None:
        raise ValueError("schema field not found in registry response")
    return json.loads(raw_schema) if isinstance(raw_schema, str) else raw_schema


def load_local_schema(path: str) -> dict:
    """
    Load JSON schema from local filesystem.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_validator(schema_registry_url: Optional[str], subject: str, local_path: Optional[str]) -> Optional[Draft7Validator]:
    """
    Try building a validator from Schema Registry; if unavailable, fallback to local schema file.
    Returns a Draft7Validator or None if both sources are unavailable.
    """
    # 1) Intento remoto (Schema Registry)
    if schema_registry_url:
        try:
            schema = fetch_schema_from_registry(schema_registry_url, subject)
            logger.info("schema_fetched", extra={"subject": subject})
            return Draft7Validator(schema)
        except Exception:
            logger.exception("fetch_schema_failed", extra={"schema_registry_url": schema_registry_url, "subject": subject})

    # 2) Fallback local
    if local_path:
        try:
            schema = load_local_schema(local_path)
            logger.info("schema_loaded_local", extra={"path": local_path})
            return Draft7Validator(schema)
        except Exception:
            logger.exception("load_local_schema_failed", extra={"path": local_path})

    logger.warning("schema_validator_unavailable; continuing_without_validation")
    return None


def main():
    # Config Schema
    SCHEMA_REGISTRY_URL = os.getenv(
        "SCHEMA_REGISTRY_URL",
        getattr(settings, "schema_registry_url", None),
    )
    NCS_SUBJECT = os.getenv("NCS_SUBJECT", "ncs-value")
    NCS_SCHEMA_LOCAL_PATH = os.getenv("NCS_SCHEMA_LOCAL_PATH", "schema/ncs_schema_registry.json")

    # Construir validador (remoto o local)
    validator = build_validator(SCHEMA_REGISTRY_URL, NCS_SUBJECT, NCS_SCHEMA_LOCAL_PATH)

    es = get_es()
    conn, ch = get_channel()

    def handle(ch, method, properties, body):
        try:
            raw = json.loads(body)
            evt = normalize(raw)
            evt_dict = evt.model_dump() if hasattr(evt, "model_dump") else dict(evt)

            # Validar contra NCS si hay validador
            if validator is not None:
                errors: List[jsonschema.ValidationError] = list(validator.iter_errors(evt_dict))
                if errors:
                    err_messages = [f"{e.message} (path: {list(e.path)})" for e in errors[:5]]
                    logger.warning("validation_failed", extra={"tenant_id": evt_dict.get("tenant_id"), "errors": err_messages})
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    try:
                        rk = getattr(method, "routing_key", None)
                    except Exception:
                        rk = None
                    logger.info("nacked_to_dlx", extra={"routing_key": rk})
                    return

            # Indexar
            index_event(es, index=f"logs-{evt.tenant_id}", body=evt_dict)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("event_indexed", extra={"tenant_id": evt.tenant_id})
        except Exception:
            logger.exception("processing_failed")
            try:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            except Exception:
                pass
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