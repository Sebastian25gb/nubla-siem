from fastapi import APIRouter, Depends, Query

from backend.app.core.auth import ensure_tenant_access, get_current_user
from backend.app.repository.elastic import get_es

router = APIRouter()


@router.get("/logs/search")
def search_logs(
    tenant: str = Query(...),
    q: str = Query("*"),
    from_: int = Query(0, alias="from"),
    size: int = Query(50),
    user=Depends(get_current_user),
):
    ensure_tenant_access(tenant, user)
    es = get_es()
    index = f"logs-{tenant}"
    body = {
        "query": {
            "bool": {
                "must": [{"query_string": {"query": q}}],
                "filter": [{"term": {"tenant_id": tenant}}],
            }
        },
        "sort": [{"@timestamp": "desc"}],
        "from": from_,
        "size": size,
    }
    res = es.search(index=index, body=body)
    return {
        "tenant": tenant,
        "query": q,
        "total": res.get("hits", {}).get("total", {}).get("value", 0),
        "hits": res.get("hits", {}).get("hits", []),
    }
