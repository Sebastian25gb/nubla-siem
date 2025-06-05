# /root/nubla-siem/backend/core/security.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from ..api.db import get_db_connection

SECRET_KEY = "nubla-siem-secret-key-1234567890"  # Mover a .env más adelante
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        tenant: str = payload.get("tenant")
        role: str = payload.get("role")
        user_id: int = payload.get("id")
        mfa_required: bool = payload.get("mfa_required", False)
        if username is None or tenant is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception from e

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, role, tenant_id FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if user is None:
                raise credentials_exception
            return {
                "id": user[0],
                "username": user[1],
                "role": user[2],
                "tenant_id": user[3],
                "tenant": tenant,
                "mfa_required": mfa_required
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {str(e)}")
    finally:
        conn.close()