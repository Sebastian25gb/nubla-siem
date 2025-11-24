from __future__ import annotations

import json
import logging
import os
import time
from typing import TYPE_CHECKING, Any, Dict, Optional

from jsonschema import Draft7Validator
from prometheus_client import Counter, Gauge, Histogram, start_http_server

from backend.app.core.config import settings
from backend.app.core.logging import configure_logging
from backend.app.infrastructure.rabbitmq import get_channel
from backend.app.processing.normalizer import normalize
from backend.app.processing.tenant_registry import get_registry, is_valid_tenant
from backend.app.processing.utils import prepare_event, top_validation_errors
from backend.app.repository.elastic import get_es, index_event

logger = logging.getLogger(__name__)

EVENTS_PROCESSED = Counter("events_processed_total", "Total events consumidos")
EVENTS_INDEXED = Counter("events_indexed_total", "Eventos indexados (unitarios o bulk)")
EVENTS_NACKED = Counter("events_nacked_total", "Eventos enviados a DLX/DLQ")
EVENTS_VALIDATION_FAILED = Counter("events_validation_failed_total", "Fallos de validación schema")
EVENTS_INDEX_FAILED = Counter("events_index_failed_total", "Fallos indexación individual")
EVENTS_BULK_FLUSHES = Counter("bulk_flushes_total", "Flush bulk realizados")

EVENTS_INDEXED_BY_TENANT = Counter(
    "events_indexed_by_tenant_total", "Eventos indexados por tenant", ["tenant_id"]
)
EVENTS_NACKED_BY_REASON = Counter(
    "events_nacked_by_reason_total", "Eventos rechazados por razón", ["reason"]
)

INDEX_LATENCY = Histogram(
    "index_latency_seconds",
    "Latencia por flush bulk o documento individual",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
)
EVENT_INDEX_LATENCY = Histogram(
    "event_index_latency_seconds",
    "Latencia de indexación por evento unitario (no bulk)",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
BUFFER_SIZE = Gauge("consumer_buffer_size", "Número de eventos en buffer bulk")

NORMALIZER_LATENCY = Histogram(
    "normalizer_latency_seconds",
    "Tiempo de normalización + mapping por evento",
    buckets=(0.0005, 0.001, 0.005, 0.01, 0.025, 0.05),
)
TENANT_REGISTRY_SIZE = Gauge("tenant_registry_size", "Número de tenants registrados")

USE_MANUAL_DLX = os.getenv("USE_MANUAL_DLX", "false").lower() == "true"
MANUAL_DLX_EXCHANGE = os.getenv("RABBITMQ_DLX", "logs_default.dlx")

USE_BULK = os.getenv("USE_BULK", "false").lower() == "true"
BULK_MAX_ITEMS = int(os.getenv("BULK_MAX_ITEMS", "500"))
BULK_MAX_INTERVAL_MS = int(os.getenv("BULK_MAX_INTERVAL_MS", "1000"))
CONSUMER_PREFETCH = int(os.getenv("CONSUMER_PREFETCH", "5"))

REQUIRE_TENANT = os.getenv("REQUIRE_TENANT", "false").lower() == "true"

SEVERITY_MAP = {
    "error": "critical",
    "alert": "high",
    "warning": "medium",
    "warn": "medium",
}

if TYPE_CHECKING:
    from backend.app.processing.bulk_indexer import (
        BulkIndexer as BulkIndexerType,  # pragma: no cover
    )

try:
    from backend.app.processing.bulk_indexer import BulkIndexer as _BulkIndexer  # type: ignore
except Exception:
    _BulkIndexer = None  # type: ignore

bulk_indexer: Optional["BulkIndexerType"] = None


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
        exchange=MANUAL_DLX_EXCHANGE,
        routing_key=routing_key,
        body=body_bytes,
        properties=props,
    )
    EVENTS_NACKED.inc()
    EVENTS_NACKED_BY_REASON.labels(reason=reason).inc()


def _normalize_severity(evt: Dict[str, Any]) -> None:
    sev = evt.get("severity")
    if isinstance(sev, str):
        sev_low = sev.lower()
        if sev_low in SEVERITY_MAP:
            evt["severity_original_mapped"] = sev_low
            evt["severity"] = SEVERITY_MAP[sev_low]
        else:
            evt["severity"] = sev_low


def validate_tenant(evt: Dict[str, Any]) -> bool:
    t = evt.get("tenant_id")
    return isinstance(t, str) and bool(t.strip())


def main() -> None:
    try:
        start_http_server(int(os.getenv("METRICS_PORT", "9109")))
        logger.info("metrics_server_started", extra={"port": os.getenv("METRICS_PORT", "9109")})
    except Exception:
        logger.warning("metrics_server_failed", exc_info=True)

    es = get_es()

    global bulk_indexer
    if USE_BULK and _BulkIndexer is not None:
        bulk_indexer = _BulkIndexer(
            client=es,
            max_items=BULK_MAX_ITEMS,
            max_interval_ms=BULK_MAX_INTERVAL_MS,
            default_pipeline="logs_ingest",
        )
        logger.info(
            "bulk_enabled",
            extra={"max_items": BULK_MAX_ITEMS, "max_interval_ms": BULK_MAX_INTERVAL_MS},
        )
    else:
        logger.info("bulk_disabled")

    schema_path = os.getenv(
        "NCS_SCHEMA_LOCAL_PATH",
        getattr(settings, "ncs_schema_local_path", "backend/app/schema/ncs_v1.0.0.json"),
    )
    validator = build_validator(schema_path)

    try:
        reg = get_registry()
        reg.load()
        TENANT_REGISTRY_SIZE.set(len(reg.all()))
        logger.info("tenant_registry_loaded")
    except Exception:
        logger.warning("tenant_registry_load_failed", exc_info=True)

    try:
        connection, channel, queue_name, exchange = get_channel()
    except Exception:
        logger.exception("rabbitmq_connection_failed")
        return

    def handle(ch, method, properties, body):
        EVENTS_PROCESSED.inc()
        try:
            start_norm = time.time()
            raw_msg = json.loads(body)
            normalized = normalize(raw_msg)

            # Leer flag de reintentos antes de prepare_event (prepare_event puede podar campos desconocidos)
            # Leer flag de reintentos antes de prepare_event (y también desde raw_msg)
            FORCE_RETRIES = bool(\n    (isinstance(normalized, dict) and (\n        normalized.get("flag_force_retries") is True or normalized.get("force_retries") is True\n    )) or\n    (isinstance(raw_msg, dict) and (\n        raw_msg.get("flag_force_retries") is True or raw_msg.get("force_retries") is True\n    ))\n)
                (isinstance(normalized, dict) and (
                    normalized.get("flag_force_retries") is True or normalized.get("force_retries") is True
                )) or
                (isinstance(raw_msg, dict) and (
                    raw_msg.get("flag_force_retries") is True or raw_msg.get("force_retries") is True
                ))
            )
            # Host→tenant mapping (override si tenant = default)
            try:
                if isinstance(normalized, dict):
                    existing_tenant = normalized.get("tenant_id")
                    host_val = (
                        normalized.get("host")
                        or normalized.get("host_name")
                        or normalized.get("original", {}).get("raw_kv", {}).get("devname")
                    )
                    if host_val:
                        host_norm = str(host_val).strip().lower().replace(" ", "-")
                        host_to_tenant = {
                            "delawarehotel": "delawarehotel",
                            "demo-host": "demo-host",
                        }
                        mapped = host_to_tenant.get(host_norm)
                        default_tenant = getattr(settings, "tenant_id", "default")
                        if mapped and (existing_tenant in (None, "", default_tenant)):
                            normalized["tenant_id"] = mapped
                            logger.info(
                                "mapped_host_to_tenant",
                                extra={
                                    "host": host_val,
                                    "previous_tenant": existing_tenant,
                                    "tenant_mapped": mapped,
                                },
                            )
            except Exception:
                logger.exception("host_to_tenant_mapping_failed")
            finally:
                NORMALIZER_LATENCY.observe(time.time() - start_norm)

            if isinstance(normalized, dict):
                evt_dict = dict(normalized)
            else:
                evt_dict = json.loads(json.dumps(normalized, default=str))

            _normalize_severity(evt_dict)

            if REQUIRE_TENANT and not validate_tenant(evt_dict):
                EVENTS_VALIDATION_FAILED.inc()
