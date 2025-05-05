from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api.schemas.tenant import Tenant, TenantBase
from core.database import get_db
from models.tenant import Tenant as TenantModel

router = APIRouter()

@router.get("/", response_model=List[Tenant])
def get_tenants(db: Session = Depends(get_db)):
    return db.query(TenantModel).all()

@router.post("/", response_model=Tenant)
def create_tenant(tenant: TenantBase, db: Session = Depends(get_db)):
    db_tenant = TenantModel(**tenant.dict())
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant