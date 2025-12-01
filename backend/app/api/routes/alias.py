from fastapi import APIRouter, Query, Depends, HTTPException
from backend.app.core.auth import get_current_user, ensure_tenant_access
from backend.app.services.alias_admin import get_alias_state

router = APIRouter()

@router.get("/alias/state")
def alias_state(
    tenant: str = Query(...),
    user=Depends(get_current_user),
):
    ensure_tenant_access(tenant, user)
    alias = f"logs-{tenant}"
    try:
        data = get_alias_state(alias)
    except Exception:
        raise HTTPException(status_code=404, detail="alias_not_found")
    data["tenant"] = tenant
    return data