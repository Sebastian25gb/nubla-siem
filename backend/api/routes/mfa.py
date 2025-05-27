from fastapi import APIRouter, HTTPException, Depends
import pyotp
import qrcode
from io import BytesIO
import base64
from pydantic import BaseModel  # Añadimos esta importación
from ..db import get_db_connection
from .auth import get_current_user, create_access_token  # Añadimos create_access_token
from datetime import timedelta

router = APIRouter()

SECRET_KEY = "your-secret-key"  # Debería coincidir con el de auth.py
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/enable-mfa")
async def enable_mfa(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id")
    username = current_user.get("username")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")

    # Generar un secreto TOTP
    totp_secret = pyotp.random_base32()

    # Guardar el secreto en la base de datos
    try:
        conn = get_db_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET mfa_secret = %s WHERE id = %s RETURNING mfa_secret",
                (totp_secret, user_id)
            )
            updated_user = cur.fetchone()
            if not updated_user:
                raise HTTPException(status_code=404, detail="User not found")
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to enable MFA: {str(e)}")
    finally:
        conn.close()

    # Generar la URI para el código QR
    totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(name=username, issuer_name="NublaSIEM")

    # Generar el código QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")

    # Convertir la imagen a base64 para enviarla al frontend
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return {"message": "MFA enabled. Scan the QR code with Microsoft Authenticator.", "qr_code": f"data:image/png;base64,{qr_code_base64}"}

class MFACode(BaseModel):
    code: str

@router.post("/verify-mfa", response_model=Token)
async def verify_mfa(mfa_code: MFACode, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id")
    username = current_user.get("username")
    role = current_user.get("role")
    tenant_id = current_user.get("tenant_id")
    mfa_required = current_user.get("mfa_required", False)

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")
    if not mfa_required:
        raise HTTPException(status_code=400, detail="MFA verification not required")

    try:
        conn = get_db_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT mfa_secret FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            if not user["mfa_secret"]:
                raise HTTPException(status_code=400, detail="MFA not enabled for this user")

            totp = pyotp.TOTP(user["mfa_secret"])
            if not totp.verify(mfa_code.code):
                raise HTTPException(status_code=401, detail="Invalid MFA code")

            # Generar el token JWT final
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user_id, "username": username, "role": role, "tenant_id": tenant_id},
                expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify MFA: {str(e)}")
    finally:
        conn.close()