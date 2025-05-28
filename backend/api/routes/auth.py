from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel  # Añadimos esta importación
import psycopg2
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

router = APIRouter()

# Configuración de seguridad
SECRET_KEY = "nubla-siem-secret-key-1234567890"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Modelo de respuesta para el token
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    mfa_required: bool

# Conexión a PostgreSQL con SSL
def get_db_connection():
    return psycopg2.connect(
        dbname="nubla_db",
        user="nubla_user",
        password="secure_password_123",
        host="postgres",
        sslmode="prefer"
    )

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
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

@router.post("/", response_model=TokenResponse)  # Cambiamos Dict[str, str] por TokenResponse
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.id, u.password_hash, u.role, t.name AS tenant_name, u.mfa_secret
                FROM users u
                JOIN tenants t ON u.tenant_id = t.id
                WHERE u.username = %s
            """, (form_data.username,))
            user = cur.fetchone()
            if not user or not verify_password(form_data.password, user[1]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Verificar si el usuario tiene MFA habilitado
            if user[4]:  # user[4] es mfa_secret
                # Generar un token temporal para el paso de MFA
                temp_token = create_access_token(
                    data={
                        "sub": form_data.username,
                        "tenant": user[3],
                        "role": user[2],
                        "id": user[0],
                        "mfa_required": True
                    },
                    expires_delta=timedelta(minutes=5)
                )
                return {"access_token": temp_token, "token_type": "bearer", "mfa_required": True}

            # Si no hay MFA, generar el token final
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": form_data.username, "tenant": user[3], "role": user[2], "id": user[0]},
                expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer", "mfa_required": False}
    finally:
        conn.close()