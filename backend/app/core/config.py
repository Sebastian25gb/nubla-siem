from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # OpenSearch-only
    opensearch_host: str = "opensearch:9200"

    # Compatibilidad temporal (código legado puede seguir leyendo elasticsearch_host)
    @property
    def elasticsearch_host(self) -> str:
        return self.opensearch_host

    # RabbitMQ
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
    ncs_schema_local_path: str = "backend/app/schema/ncs_v1.0.0.json"

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

settings = Settings()