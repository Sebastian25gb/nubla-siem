from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ELASTICSEARCH_HOST: str = "elasticsearch"
    ELASTICSEARCH_PORT: str = "9200"
    ELASTICSEARCH_USER: str = "elastic"
    ELASTICSEARCH_PASSWORD: str = "yourpassword"
    POSTGRES_USER: str = "nubla_user"
    POSTGRES_PASSWORD: str = "secure_password_123"
    POSTGRES_DB: str = "nubla_db"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: str = "5432"
    REDIS_HOST: str = "redis"
    REDIS_PORT: str = "6379"
    SECRET_KEY: str = "your-secret-key"  # Cambiar por una clave segura en producción
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()