import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(
        dbname="nubla_db",
        user="nubla_user",
        password="secure_password_123",
        host="postgres",
        port="5432",
        cursor_factory=RealDictCursor
    )