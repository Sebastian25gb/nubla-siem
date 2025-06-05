# /root/nubla-siem/backend/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    ELASTICSEARCH_HOST: str
    ELASTICSEARCH_PORT: str
    ELASTICSEARCH_USER: str
    ELASTICSEARCH_PASSWORD: str
    REDIS_HOST: str
    REDIS_PORT: str
    TWILIO_SID: str
    TWILIO_TOKEN: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()