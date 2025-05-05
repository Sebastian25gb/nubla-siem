from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings
import time
from sqlalchemy.exc import OperationalError

SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# Intentar conectar a la base de datos con más reintentos
for attempt in range(15):  # Aumentar a 15 intentos
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        engine.connect()  # Probar la conexión
        break
    except OperationalError as e:
        print(f"Failed to connect to PostgreSQL, attempt {attempt + 1}/15: {e}")
        if attempt < 14:
            time.sleep(10)  # Mantener 10 segundos de espera
        else:
            raise e

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()