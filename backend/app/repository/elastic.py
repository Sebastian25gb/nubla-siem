import logging
from typing import Optional, Any, Dict

from core.config import settings

# Intentamos importar ambos clientes; usamos el que corresponda según el host.
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
    """
    Normaliza la variable ELASTICSEARCH_HOST para devolver una URL completa.
    Casos aceptados:
      - http(s)://host:port  (se usa tal cual)
      - host:port            -> se antepone http://
      - host                 -> se antepone http:// y puerto 9200 si no hay puerto
    """
    fallback = "http://elasticsearch:9200"
    if not raw:
        return fallback
    raw = raw.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    # Si incluye puerto
    if ":" in raw:
        return f"http://{raw}"
    return f"http://{raw}:9200"


def _is_opensearch(url: str) -> bool:
    """
    Heurística simple: si el host incluye la palabra 'opensearch' asumimos OpenSearch.
    """
    return "opensearch" in url.lower()


def get_es():
    """
    Devuelve un cliente listo para indexar (OpenSearch o Elasticsearch).
    Mantiene el nombre por compatibilidad con código existente.
    """
    host_setting = getattr(settings, "elasticsearch_host", None)
    url = _normalize_url(host_setting)

    if _is_opensearch(url) and OpenSearch:
        logger.info("using_opensearch_client", extra={"url": url})
        return OpenSearch(
            hosts=[url],
            timeout=30,
        )
    if Elasticsearch:
        logger.info("using_elasticsearch_client", extra={"url": url})
        return Elasticsearch(url, request_timeout=30)

    raise RuntimeError("No hay cliente disponible (ni opensearch-py ni elasticsearch instalado).")


def index_event(es_client, index: str, body: Dict[str, Any], refresh: Optional[str] = None) -> Dict[str, Any]:
    """
    Indexa un documento en el índice dado. Para OpenSearch y Elasticsearch funciona igual,
    salvo que el cliente OpenSearch usa 'body' y el de Elasticsearch (>=8) acepta 'document'.
    Detectamos el tipo de cliente dinámicamente.
    """
    params = {}
    if refresh:
        params["refresh"] = refresh

    try:
        # OpenSearchPy usa 'body'; Elasticsearch python >=8 usa 'document'.
        if OpenSearch and isinstance(es_client, OpenSearch):
            resp = es_client.index(index=index, body=body, params=params)
        else:
            # Cliente Elasticsearch
            resp = es_client.index(index=index, document=body, params=params)
        logger.debug("indexed_event", extra={"index": index, "result": resp.get("result")})
        return resp
    except (OpenSearchException, ElasticsearchException, Exception):
        logger.exception("es_index_failed", extra={"index": index})
        raise