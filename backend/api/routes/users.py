from fastapi import APIRouter, HTTPException, Depends
from ..db import get_db_connection
from .auth import get_current_user
import bcrypt

router = APIRouter()

@router.get("/users")
async def list_users(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can list users")

    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID not found in token")

    try:
        conn = get_db_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.username, u.email, u.role, u.tenant_id, t.name as tenant_name
                FROM users u
                JOIN tenants t ON u.tenant_id = t.id
                WHERE u.tenant_id = %s
                """,
                (tenant_id,)
            )
            users = cur.fetchall()
            return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")
    finally:
        conn.close()

@router.get("/users/{user_id}")
async def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view users")

    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID not found in token")

    try:
        conn = get_db_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.username, u.email, u.role, u.tenant_id, t.name as tenant_name
                FROM users u
                JOIN tenants t ON u.tenant_id = t.id
                WHERE u.id = %s AND u.tenant_id = %s
                """,
                (user_id, tenant_id)
            )
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found or not in your tenant")
            return {"user": user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {str(e)}")
    finally:
        conn.close()

@router.put("/users/{user_id}")
async def update_user(user_id: int, user_update: dict, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update users")

    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID not found in token")

    try:
        conn = get_db_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

    try:
        with conn.cursor() as cur:
            # Check if user exists and belongs to the tenant
            cur.execute(
                "SELECT 1 FROM users WHERE id = %s AND tenant_id = %s",
                (user_id, tenant_id)
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="User not found or not in your tenant")

            # Update user fields
            update_fields = []
            update_values = []
            if "email" in user_update:
                update_fields.append("email = %s")
                update_values.append(user_update["email"])
            if "role" in user_update:
                if user_update["role"] not in ['admin', 'user', 'analyst']:
                    raise HTTPException(status_code=400, detail="Invalid role")
                update_fields.append("role = %s")
                update_values.append(user_update["role"])
            if "password" in user_update:
                hashed_password = bcrypt.hashpw(user_update["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                update_fields.append("password_hash = %s")
                update_values.append(hashed_password)

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")

            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s AND tenant_id = %s"
            update_values.extend([user_id, tenant_id])

            cur.execute(update_query, update_values)
            conn.commit()
            return {"message": "User updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")
    finally:
        conn.close()

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID not found in token")

    try:
        conn = get_db_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

    try:
        with conn.cursor() as cur:
            # Check if user exists and belongs to the tenant
            cur.execute(
                "SELECT 1 FROM users WHERE id = %s AND tenant_id = %s",
                (user_id, tenant_id)
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="User not found or not in your tenant")

            # Delete the user
            cur.execute("DELETE FROM users WHERE id = %s AND tenant_id = %s", (user_id, tenant_id))
            conn.commit()
            return {"message": "User deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
    finally:
        conn.close()