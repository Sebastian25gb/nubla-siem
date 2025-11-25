from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models import User, UserTenantRole
from backend.app.core.security import verify_password, create_access_token

router = APIRouter()

class LoginIn(BaseModel):
    username: str
    password: str

@router.post("/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    roles = db.query(UserTenantRole).filter(UserTenantRole.user_id == user.id).all()
    tenants = [r.tenant_id for r in roles]
    token = create_access_token(subject=str(user.id), claims={"tenants": tenants, "username": user.username})
    return {"access_token": token, "token_type": "bearer", "tenants": tenants}