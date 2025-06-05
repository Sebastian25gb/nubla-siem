# /root/nubla-siem/backend/api/db.py
import psycopg2
from psycopg2.extras import RealDictCursor
from core.config import settings

def get_db_connection():
    return psycopg2.connect(
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        cursor_factory=RealDictCursor
    )