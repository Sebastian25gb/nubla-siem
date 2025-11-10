from typing import Optional, Any, Dict
import logging

# The modern elasticsearch client exposes exceptions in elasticsearch.exceptions
# Import Elasticsearch and try to import ElasticsearchException from the exceptions module.
# If that import fails (very old/new clients), fall back to a generic Exception to avoid import errors.
try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import ElasticsearchException
except Exception:
    # Fallback: import only the client and alias a generic exception for compatibility
    from elasticsearch import Elasticsearch  # type: ignore
    ElasticsearchException = Exception  # type: ignore

from core.config import settings

logger = logging.getLogger(__name__)


def _normalize_es_url(es_host: Optional[str]) -> str:
    """
    Normalize different ELASTICSEARCH_HOST values into a full URL:
      - If es_host is None -> return http://elasticsearch:9200 (fallback)
      - If es_host starts with http:// or https:// -> return as-is
      - If es_host is host:port or host -> prepend http://
    """
    fallback = "http://elasticsearch:9200"
    if not es_host:
        return fallback

    es_host = str(es_host).strip()

    # Already a full URL
    if es_host.startswith("http://") or es_host.startswith("https://"):
        return es_host

    # Otherwise assume host or host:port -> prepend http://
    return f"http://{es_host}"


def get_es() -> Elasticsearch:
    """
    Return an Elasticsearch client. The settings.elasticsearch_host may be any of:
      - "elasticsearch" (no port) -> http://elasticsearch:9200
      - "opensearch:9200" -> http://opensearch:9200
      - "http://opensearch:9200" -> used as-is
      - "https://es.example.com:9243" -> used as-is
    """
    es_host_setting = getattr(settings, "elasticsearch_host", None)
    url = _normalize_es_url(es_host_setting)
    # Use a small default timeout; add verify_certs or auth if you need it later
    return Elasticsearch(url, request_timeout=30)


def index_event(es_client: Elasticsearch, index: str, body: Dict[str, Any], refresh: Optional[str] = None) -> Dict[str, Any]:
    """
    Index a document into the given index. Returns the raw response from Elasticsearch.
    - es_client: instance returned by get_es()
    - index: index name (e.g. "logs-default-000001" or "logs-default")
    - body: JSON-serializable document
    - refresh: if "wait_for" will wait for the document to be searchable
    """
    try:
        params = {}
        if refresh:
            params["refresh"] = refresh
        # modern elasticsearch client uses 'document' kwarg
        resp = es_client.index(index=index, document=body, params=params)
        logger.debug("indexed_event", extra={"index": index, "resp": resp})
        return resp
    except ElasticsearchException:
        logger.exception("es_index_failed", extra={"index": index})
        raise