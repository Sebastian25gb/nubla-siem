import json
import logging
import os
import signal
from typing import Any, List

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
    try:
        url = f"{schema_registry_url.rstrip('/')}/subjects/{subject}/versions/latest"
        logger.info("fetching_schema", extra={"url": url})
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        # payload['schema'] is a JSON string in many registries
        raw_schema = payload.get("schema")
        if raw_schema is None:
            raise ValueError("schema field not found in registry response")
        # Some registries wrap schema as a string; parse it
        if isinstance(raw_schema, str):
            schema_obj = json.loads(raw_schema)
        else:
            schema_obj = raw_schema
        logger.info("schema_fetched", extra={"subject": subject, "version": payload.get("version")})
        return schema_obj
    except Exception:
        logger.exception("fetch_schema_failed", extra={"schema_registry_url": schema_registry_url, "subject": subject})
        raise


def build_validator(schema_registry_url: str, subject: str) -> Draft7Validator:
    schema = fetch_schema_from_registry(schema_registry_url, subject)
    validator = Draft7Validator(schema)
    return validator


def main():
    # Schema Registry config (can be provided via env or .env)
    SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", settings.schema_registry_url if hasattr(settings, "schema_registry_url") else "http://schema-registry:8081")
    NCS_SUBJECT = os.getenv("NCS_SUBJECT", "ncs-value")

    # Try to fetch validator at startup. If fails, continue without validator but log warning.
    validator = None
    try:
        validator = build_validator(SCHEMA_REGISTRY_URL, NCS_SUBJECT)
    except Exception:
        logger.warning("schema_validator_unavailable; continuing_without_validation")

    es = get_es()
    conn, ch = get_channel()

    def handle(ch, method, properties, body):
        try:
            raw = json.loads(body)
            evt = normalize(raw)
            evt_dict = evt.model_dump() if hasattr(evt, "model_dump") else dict(evt)

            # Validate against NCS schema if validator available
            if validator is not None:
                errors: List[jsonschema.ValidationError] = list(validator.iter_errors(evt_dict))
                if errors:
                    # Log first errors and nack to DLX (no requeue) to avoid processing loops
                    err_messages = [f"{e.message} (path: {list(e.path)})" for e in errors[:5]]
                    logger.warning("validation_failed", extra={"tenant_id": evt_dict.get("tenant_id"), "errors": err_messages})
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    try:
                        rk = getattr(method, "routing_key", None)
                    except Exception:
                        rk = None
                    logger.info("nacked_to_dlx", extra={"routing_key": rk})
                    return

            # Index event in OpenSearch/Elasticsearch
            index_event(es, index=f"logs-{evt.tenant_id}", body=evt_dict)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("event_indexed", extra={"tenant_id": evt.tenant_id})
        except Exception:
            logger.exception("processing_failed")
            # Evitar loops: mandar a DLX (nack sin requeue)
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