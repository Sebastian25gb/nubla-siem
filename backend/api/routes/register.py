from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import bcrypt
from ..db import get_db_connection

router = APIRouter()

class UserRegister(BaseModel):
    username: str
    password: str
    email: str | None = None
    role: str

@router.post("/register")
async def register_user(user: UserRegister):
    # Validate role
    if user.role not in ['admin', 'user', 'analyst']:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin', 'user', or 'analyst'")

    # Hash the password
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Connect to the database
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check if username already exists
            cur.execute("SELECT 1 FROM users WHERE username = %s", (user.username,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Username already exists")

            # Check if tenant_id exists (using personal tenant_id: 11)
            tenant_id = 11  # Tenant 'personal'
            cur.execute("SELECT 1 FROM tenants WHERE id = %s", (tenant_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=400, detail="Tenant does not exist")

            # Insert the new user
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
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register user: {str(e)}")
    finally:
        conn.close()
