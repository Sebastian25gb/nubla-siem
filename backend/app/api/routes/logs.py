from fastapi import APIRouter, Query
from backend.app.repository.elastic import get_es

router = APIRouter()

@router.get("/logs/search")
def search_logs(
    tenant: str = Query(...),
    q: str = Query("*"),
    from_: int = Query(0, alias="from"),
    size: int = Query(50),
):
    es = get_es()
    index = f"logs-{tenant}"
    body = {
        "query": {"bool": {"must": [{"query_string": {"query": q}}], "filter": [{"term": {"tenant_id": tenant}}]}},
        "sort": [{"@timestamp": "desc"}],
        "from": from_,
        "size": size,
    }
    res = es.search(index=index, body=body)
    return {"total": res.get("hits", {}).get("total", {}).get("value", 0), "hits": res.get("hits", {}).get("hits", [])}