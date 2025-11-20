import logging
import os
from typing import Optional, Any, Dict, Tuple

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

def _normalize_url(raw: Optional[str]) -> str:
    """
    Normaliza un host o URL a un endpoint http://host:port
    Fallback por defecto a opensearch en red de docker-compose.
    """
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
    """
    Se soportan OS_USER/OS_PASS. (ES_USER/ES_PASS quedan deprecadas pero se leen si existen)
    """
    user = os.getenv("OS_USER") or os.getenv("ES_USER")
    pwd  = os.getenv("OS_PASS") or os.getenv("ES_PASS")
    if user and pwd:
        return user, pwd
    return None, None  # sin auth por defecto

def get_es():
    """
    Retorna cliente OpenSearch. (Nombre legado por compatibilidad de imports)
    """
    raw = os.getenv("OPENSEARCH_HOST") or getattr(settings, "opensearch_host", None) \
          or os.getenv("ELASTICSEARCH_HOST") or getattr(settings, "elasticsearch_host", None)
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

    try:
        return es_client.index(index=index, body=body, params=params)
    except Exception as e:
        logger.exception("os_index_failed", extra={"index": index, "error": str(e)})
        raise