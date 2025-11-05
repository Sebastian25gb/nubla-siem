from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    elasticsearch_host: str = "elasticsearch"

    rabbitmq_host: str = "rabbitmq"
    rabbitmq_user: str = "admin"
    rabbitmq_password: str = "securepass"
    rabbitmq_exchange: str = "logs_default"
    rabbitmq_queue: str = "nubla_logs_default"
    rabbitmq_routing_key: str = "nubla.log.default"

    tenant_id: str = "default"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

settings = Settings()