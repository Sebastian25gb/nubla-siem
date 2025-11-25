from fastapi import APIRouter, Query, Depends, HTTPException
from backend.app.repository.elastic import get_es
from backend.app.core.auth import get_current_user, ensure_tenant_access

router = APIRouter()

@router.get("/alias/state")
def alias_state(
    tenant: str = Query(...),
    user=Depends(get_current_user),
):
    ensure_tenant_access(tenant, user)
    es = get_es()
    alias = f"logs-{tenant}"

    # Obtener alias
    try:
        alias_data = es.indices.get_alias(name=alias)
    except Exception:
        raise HTTPException(status_code=404, detail="alias_not_found")

    indices = []
    write_index = None
    for idx, data in alias_data.items():
        is_write = data["aliases"][alias].get("is_write_index", False)
        indices.append({"index": idx, "is_write_index": is_write})
        if is_write:
            write_index = idx

    # Explicación ISM del write index
    explain = None
    if write_index:
        try:
            explain_raw = es.transport.perform_request(
                "GET", f"/_plugins/_ism/explain/{write_index}"
            )
            explain = explain_raw.get(write_index)
        except Exception:
            explain = {"error": "explain_failed"}

    return {
        "alias": alias,
        "tenant": tenant,
        "write_index": write_index,
        "indices": indices,
        "explain": explain,
    }