from typing import Optional
from elasticsearch import Elasticsearch
from core.config import settings


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
    return Elasticsearch(url)