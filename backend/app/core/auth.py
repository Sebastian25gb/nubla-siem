import os
from typing import List

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

JWT_SECRET = os.getenv("JWT_SECRET", "changeme-super-secret")
JWT_ALG = os.getenv("JWT_ALG", "HS256")

bearer = HTTPBearer(auto_error=True)


class CurrentUser:
    def __init__(self, user_id: str, username: str, tenants: List[str]):
        self.user_id = user_id
        self.username = username
        self.tenants = tenants


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> CurrentUser:
    token = creds.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid_token")
    sub = payload.get("sub")
    username = payload.get("username")
    tenants = payload.get("tenants", [])
    if not sub or not username:
        raise HTTPException(status_code=401, detail="invalid_claims")
    return CurrentUser(user_id=sub, username=username, tenants=tenants)


def ensure_tenant_access(tenant_id: str, user: CurrentUser):
    if tenant_id not in user.tenants:
        raise HTTPException(status_code=403, detail="tenant_forbidden")
