from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.models import Tenant
from backend.app.db.session import get_db

router = APIRouter()


@router.get("/tenants")
def list_tenants(db: Session = Depends(get_db)):
    items = db.query(Tenant).filter(Tenant.active == True).all()  # noqa: E712
    return [t.id for t in items]
