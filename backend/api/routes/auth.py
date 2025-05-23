from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict
import psycopg2
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
from datetime import datetime, timedelta

router = APIRouter()

# Configuración de seguridad
SECRET_KEY = "nubla-siem-secret-key-1234567890"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

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
        if username is None or tenant is None:
            raise credentials_exception
        return {"username": username, "tenant": tenant, "role": role}
    except JWTError:
        raise credentials_exception

@router.post("/", response_model=Dict[str, str])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Obtener el usuario y el nombre del tenant
            cur.execute("""
                SELECT u.password_hash, u.role, t.name AS tenant_name
                FROM users u
                JOIN tenants t ON u.tenant_id = t.id
                WHERE u.username = %s
            """, (form_data.username,))
            user = cur.fetchone()
            if not user or not verify_password(form_data.password, user[0]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            # Guardar el nombre del tenant y el rol en el token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": form_data.username, "tenant": user[2], "role": user[1]},
                expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}
    finally:
        conn.close()