import logging
import time
from typing import Any, Dict, Optional

from backend.app.core.opensearch_client import get_client
from backend.app.metrics.counters import INDEX_RETRIES

logger = logging.getLogger(__name__)

def get_es():
    return get_client()

def index_event(
    es_client,
    index: str,
    body: Dict[str, Any],
    refresh: Optional[str] = None,
    pipeline: Optional[str] = None,
    ensure_required: bool = True,
    retries: int = 3,
    backoff_seconds: float = 0.5,
) -> Dict[str, Any]:
    if ensure_required:
        body.setdefault("schema_version", "1.0.0")
        body.setdefault("dataset", "generic.unknown")
        if "@timestamp" not in body and "timestamp" in body:
            body["@timestamp"] = body["timestamp"]

    params: Dict[str, Any] = {}
    if refresh:
        params["refresh"] = refresh
    if pipeline:
        params["pipeline"] = pipeline

    attempt = 0
    last_err: Optional[Exception] = None
    while attempt <= retries:
        try:
            return es_client.index(index=index, body=body, params=params)
        except Exception as e:
            last_err = e
            logger.warning(
                "os_index_retry",
                extra={"index": index, "attempt": attempt, "error": str(e)},
            )
            if attempt == retries:
                logger.exception("os_index_failed_final", extra={"index": index, "error": str(e)})
                raise
            INDEX_RETRIES.inc()
            time.sleep(backoff_seconds * (attempt + 1))
            attempt += 1
    raise last_err if last_err else RuntimeError("Unknown indexing failure")