import logging
from typing import Optional, Any, Dict

from core.config import settings

try:
    from opensearchpy import OpenSearch
    from opensearchpy.exceptions import OpenSearchException
except Exception:
    OpenSearch = None  # type: ignore
    OpenSearchException = Exception  # type: ignore

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import ElasticsearchException
except Exception:
    Elasticsearch = None  # type: ignore
    ElasticsearchException = Exception  # type: ignore

logger = logging.getLogger(__name__)


def _normalize_url(raw: Optional[str]) -> str:
    fallback = "http://elasticsearch:9200"
    if not raw:
        return fallback
    raw = raw.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    if ":" in raw:
        return f"http://{raw}"
    return f"http://{raw}:9200"


def _is_opensearch(url: str) -> bool:
    return "opensearch" in url.lower()


def get_es():
    host_setting = getattr(settings, "elasticsearch_host", None)
    url = _normalize_url(host_setting)
    if _is_opensearch(url) and OpenSearch:
        logger.info("using_opensearch_client", extra={"url": url})
        return OpenSearch(hosts=[url], timeout=30)
    if Elasticsearch:
        logger.info("using_elasticsearch_client", extra={"url": url})
        return Elasticsearch(url, request_timeout=30)
    raise RuntimeError("No search client installed.")


def index_event(
    es_client,
    index: str,
    body: Dict[str, Any],
    refresh: Optional[str] = None,
    pipeline: Optional[str] = None,
    ensure_required: bool = True,
) -> Dict[str, Any]:
    """
    Indexa un documento en OpenSearch/Elasticsearch.
    - pipeline: nombre de ingest pipeline a aplicar
    - ensure_required: rellena campos mínimos si faltan (@timestamp, dataset, schema_version)
    """
    if ensure_required:
        if "@timestamp" not in body and "timestamp" in body:
            body["@timestamp"] = body["timestamp"]
        if "schema_version" not in body:
            body["schema_version"] = "1.0.0"
        if "dataset" not in body:
            body["dataset"] = "generic.unknown"

    params: Dict[str, Any] = {}
    if refresh:
        params["refresh"] = refresh
    if pipeline:
        params["pipeline"] = pipeline

    try:
        if OpenSearch and isinstance(es_client, OpenSearch):
            resp = es_client.index(index=index, body=body, params=params)
        else:
            resp = es_client.index(index=index, document=body, params=params)
        logger.debug("indexed_event", extra={"index": index, "result": resp.get("result")})
        return resp
    except (OpenSearchException, ElasticsearchException, Exception):
        logger.exception("es_index_failed", extra={"index": index})
        raise