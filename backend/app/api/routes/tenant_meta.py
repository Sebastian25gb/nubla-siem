from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.auth import ensure_tenant_access, get_current_user
from backend.app.db.models import Tenant
from backend.app.db.session import get_db

router = APIRouter()


@router.get("/tenants/{tenant_id}/meta")
def tenant_meta(tenant_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_tenant_access(tenant_id, user)
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="tenant_not_found")
    return {
        "id": t.id,
        "display_name": t.display_name,
        "policy_id": t.policy_id,
        "active": t.active,
        "retention_class": getattr(t, "retention_class", None),
    }
