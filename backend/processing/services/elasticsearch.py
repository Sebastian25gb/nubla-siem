from elasticsearch import Elasticsearch, NotFoundError

def get_logs(es: Elasticsearch, tenant_id: str):
    """
    Busca logs en Elasticsearch para un tenant específico.
    
    Args:
        es: Cliente Elasticsearch.
        tenant_id: ID del tenant.
    
    Returns:
        Lista de logs.
    """
    try:
        index_name = f"nubla-logs-{tenant_id}"
        if not es.indices.exists(index=index_name):
            print(f"Index {index_name} does not exist. Returning empty list.")
            return []
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