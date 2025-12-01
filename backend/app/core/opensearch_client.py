import os
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple
from opensearchpy import OpenSearch
from backend.app.core.config import settings

def _normalize_url(raw: Optional[str]) -> str:
    raw = (raw or "").strip()
    if not raw:
        return settings.opensearch_host
    if raw.startswith(("http://", "https://")):
        return raw
    if ":" in raw:
        return f"http://{raw}"
    return f"http://{raw}:9200"

def _get_auth() -> Tuple[Optional[str], Optional[str]]:
    user = os.getenv("OS_USER")
    pwd = os.getenv("OS_PASS")
    if user and pwd:
        return user, pwd
    return None, None

@lru_cache(maxsize=1)
def get_client() -> OpenSearch:
    url = _normalize_url(os.getenv("OPENSEARCH_HOST") or settings.opensearch_host)
    user, pwd = _get_auth()
    kwargs: Dict[str, Any] = {"hosts": [url], "timeout": 30}
    if user and pwd:
        kwargs["http_auth"] = (user, pwd)
    client = OpenSearch(**kwargs)
    client.info()  # sanity check once
    return client