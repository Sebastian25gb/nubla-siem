from fastapi import APIRouter, Depends, HTTPException, Path
from backend.app.repository.elastic import get_es
from backend.app.core.auth import get_current_user, ensure_tenant_access

router = APIRouter()

@router.get("/tenants/{tenant_id}/stats")
def tenant_stats(
    tenant_id: str = Path(...),
    user=Depends(get_current_user),
):
    ensure_tenant_access(tenant_id, user)
    es = get_es()
    alias = f"logs-{tenant_id}"

    try:
        alias_data = es.indices.get_alias(name=alias)
    except Exception:
        raise HTTPException(status_code=404, detail="alias_not_found")

    total_docs = 0
    indices_stats = []
    for idx in alias_data.keys():
        try:
            c = es.count(index=idx)
            count = c.get("count", 0)
        except Exception:
            count = None
        indices_stats.append({"index": idx, "docs": count})
        if isinstance(count, int):
            total_docs += count

    return {
        "tenant_id": tenant_id,
        "alias": alias,
        "total_docs": total_docs,
        "indices": indices_stats,
    }