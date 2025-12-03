import os
from functools import lru_cache
from typing import Any, Dict

from opensearchpy import OpenSearch

OPENSEARCH_DEFAULT = os.getenv("OPENSEARCH_HOST", "http://opensearch:9200")
OS_USER = os.getenv("OS_USER")
OS_PASS = os.getenv("OS_PASS")


@lru_cache(maxsize=1)
def get_client() -> OpenSearch:
    kwargs: Dict[str, Any] = {"hosts": [OPENSEARCH_DEFAULT], "timeout": 30}
    if OS_USER and OS_PASS:
        kwargs["http_auth"] = (OS_USER, OS_PASS)
    client = OpenSearch(**kwargs)
    client.info()
    return client
