from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional

class Settings(BaseSettings):
    # Elasticsearch settings
    ELASTICSEARCH_HOST: str = "elasticsearch"
    ELASTICSEARCH_PORT: str = "9200"
    ELASTICSEARCH_USER: str = "elastic"
    ELASTICSEARCH_PASSWORD: str = "yourpassword"

    # PostgreSQL settings
    POSTGRES_USER: str = "nubla_user"
    POSTGRES_PASSWORD: str = "secure_password_123"
    POSTGRES_DB: str = "nubla_db"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: str = "5432"

    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: str = "6379"

    # JWT settings
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # RabbitMQ settings
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: str = "5672"
    RABBITMQ_QUEUE: str = "nubla_logs_default"
    RABBITMQ_EXCHANGE: str = "logs_default"
    RABBITMQ_ROUTING_KEY: str = "nubla.log.default"
    RABBITMQ_USER: str = "admin"
    RABBITMQ_PASSWORD: str = "securepass"
    RABBITMQ_VHOST: str = "/"

    # Tenant settings
    TENANT_ID: Optional[str] = "default"

    # Twilio settings
    TWILIO_SID: str = "your_twilio_sid"
    TWILIO_TOKEN: str = "your_twilio_token"

    @validator("RABBITMQ_PORT")
    def validate_rabbitmq_port(cls, v):
        try:
            port = int(v)
            if not (1 <= port <= 65535):
                raise ValueError("Port must be between 1 and 65535")
            return v
        except ValueError:
            raise ValueError("RABBITMQ_PORT must be a valid integer")

    @validator("TENANT_ID")
    def validate_tenant_id(cls, v):
        if v is not None and not v.strip():
            raise ValueError("TENANT_ID cannot be empty or whitespace")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "forbid"  # Prohibir variables de entorno no definidas

settings = Settings()