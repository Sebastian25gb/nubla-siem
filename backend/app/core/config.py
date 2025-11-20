from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Para desarrollo local apuntar a OpenSearch (ajusta si usas ES)
    elasticsearch_host: str = "opensearch:9200"

    # RabbitMQ: usar 127.0.0.1 si el puerto está mapeado al host, se puede sobrescribir con env
    rabbitmq_host: str = "127.0.0.1"
    rabbitmq_user: str = "admin"
    rabbitmq_password: str = "securepass"
    rabbitmq_exchange: str = "logs_default"
    rabbitmq_queue: str = "nubla_logs_default"
    rabbitmq_routing_key: str = "nubla.log.default"
    rabbitmq_dlx: str = "logs_default.dlx"

    tenant_id: str = "default"
    log_level: str = "INFO"

    # Schema local path (puede sobreescribirse con NCS_SCHEMA_LOCAL_PATH)
    ncs_schema_local_path: str = "backend/app/schema/ncs_schema_registry.json"

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

settings = Settings()