from elasticsearch import Elasticsearch
from core.config import settings
import time
from elasticsearch.exceptions import ConnectionError

# Intentar conectar a Elasticsearch con más reintentos
for attempt in range(15):  # Aumentar a 15 intentos
    try:
        es = Elasticsearch(
            [f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
            basic_auth=(settings.ELASTICSEARCH_USER, settings.ELASTICSEARCH_PASSWORD)
        )
        es.info()  # Probar la conexión
        break
    except ConnectionError as e:
        print(f"Failed to connect to Elasticsearch, attempt {attempt + 1}/15: {e}")
        if attempt < 14:
            time.sleep(10)  # Mantener 10 segundos de espera
        else:
            raise e

def get_logs(tenant_id: str):
    query = {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"tenant_id": tenant_id}}
                ]
            }
        }
    }
    response = es.search(index=f"logs-{tenant_id}", body=query, size=1000)
    return [hit["_source"] for hit in response["hits"]["hits"]]