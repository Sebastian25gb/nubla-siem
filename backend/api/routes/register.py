from fastapi import APIRouter, HTTPException, Request  # Añadimos Request
from pydantic import BaseModel
import bcrypt
from ..db import get_db_connection
import psycopg2
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class UserRegister(BaseModel):
    username: str
    password: str
    email: str | None = None
    role: str
    tenant_name: str

@router.post("/register")
@limiter.limit("5/minute")
async def register_user(user: UserRegister, request: Request):  # Añadimos request
    if user.role not in ['admin', 'user', 'analyst']:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin', 'user', or 'analyst'")

    try:
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to hash password: {str(e)}")

    try:
        conn = get_db_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE username = %s", (user.username,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Username already exists")

            cur.execute("SELECT id FROM tenants WHERE name = %s", (user.tenant_name,))
            tenant = cur.fetchone()
            if tenant:
                tenant_id = tenant['id']
            else:
                cur.execute(
                    "INSERT INTO tenants (name) VALUES (%s) RETURNING id",
                    (user.tenant_name,)
                )
                tenant_id = cur.fetchone()['id']

            cur.execute(
                """
                INSERT INTO users (username, password_hash, email, role, tenant_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, username, tenant_id
                """,
                (user.username, hashed_password, user.email, user.role, tenant_id)
            )
            new_user = cur.fetchone()
            conn.commit()
            return {"message": "User registered successfully", "user": new_user}
    except psycopg2.errors.UniqueViolation as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Username or tenant name already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register user: {str(e)}")
    finally:
        conn.close()