import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

from backend.app.core.config import settings
from backend.app.metrics.counters import INDEX_RETRIES

logger = logging.getLogger(__name__)


def _normalize_url(raw: Optional[str]) -> str:
    fallback = "http://opensearch:9200"
    raw = (raw or "").strip()
    if not raw:
        return fallback
    if raw.startswith(("http://", "https://")):
        return raw
    if ":" in raw:
        return f"http://{raw}"
    return f"http://{raw}:9200"


def _get_auth() -> Tuple[Optional[str], Optional[str]]:
    user = os.getenv("OS_USER") or os.getenv("ES_USER")
    pwd = os.getenv("OS_PASS") or os.getenv("ES_PASS")
    if user and pwd:
        return user, pwd
    return None, None


def get_es():
    raw = (
        os.getenv("OPENSEARCH_HOST")
        or getattr(settings, "opensearch_host", None)
        or os.getenv("ELASTICSEARCH_HOST")
        or getattr(settings, "elasticsearch_host", None)
    )
    url = _normalize_url(raw)
    user, pwd = _get_auth()

    from opensearchpy import OpenSearch  # type: ignore

    kwargs: Dict[str, Any] = {"hosts": [url], "timeout": 30}
    if user and pwd:
        kwargs["http_auth"] = (user, pwd)
    client = OpenSearch(**kwargs)
    client.info()
    logger.info("using_opensearch_client", extra={"url": url})
    return client


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
