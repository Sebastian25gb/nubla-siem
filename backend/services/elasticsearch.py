from elasticsearch import Elasticsearch, NotFoundError
import os
import time

ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
es = Elasticsearch([f"http://{ELASTICSEARCH_HOST}:9200"])

def wait_for_elasticsearch():
    retries = 15
    for i in range(retries):
        try:
            if es.ping():
                health = es.cluster.health(wait_for_status="green", timeout="30s")
                if health["status"] in ["green", "yellow"]:
                    print("Elasticsearch is ready with status:", health["status"])
                    return True
        except Exception as e:
            print(f"Failed to connect to Elasticsearch, attempt {i+1}/{retries}: {str(e)}")
        time.sleep(5)
    raise Exception("Could not connect to Elasticsearch after multiple attempts")

wait_for_elasticsearch()

def get_logs(tenant_id: str):
    try:
        # Verificar si el índice existe
        index_name = f"logs-{tenant_id}"
        if not es.indices.exists(index=index_name):
            print(f"Index {index_name} does not exist. Returning empty list.")
            return []

        # Realizar la búsqueda
        result = es.search(
            index=index_name,
            body={"query": {"match_all": {}}},
            size=1000
        )
        hits = result["hits"]["hits"]
        logs = [hit["_source"] for hit in hits]
        print(f"Retrieved {len(logs)} logs from index {index_name}")
        return logs
    except NotFoundError as e:
        print(f"Index {index_name} not found: {str(e)}")
        return []
    except Exception as e:
        print(f"Error fetching logs from Elasticsearch: {str(e)}")
        raise Exception(f"Error fetching logs from Elasticsearch: {str(e)}")