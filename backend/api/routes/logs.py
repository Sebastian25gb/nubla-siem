from fastapi import APIRouter, Depends, HTTPException
from elasticsearch import AsyncElasticsearch, RequestError, ConnectionError
from elasticsearch.exceptions import NotFoundError
from .auth import get_current_user
from models.logs import Log

router = APIRouter()

# Cliente de Elasticsearch
es = AsyncElasticsearch(
    hosts=["http://elasticsearch:9200"],
    basic_auth=("elastic", "yourpassword"),
    timeout=30,
    retry_on_timeout=True
)

@router.get("/", response_model=list[Log])
async def fetch_logs(before: str = None, current_user: dict = Depends(get_current_user)):
    tenant_id = current_user.get("tenant")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID not found in token")

    index_name = f"nubla-logs-{tenant_id}"

    try:
        # Verificar conexión a Elasticsearch
        if not await es.ping():
            raise HTTPException(status_code=503, detail="Elasticsearch is not available")

        # Verificar si el índice existe
        if not await es.indices.exists(index=index_name):
            return []

        # Construir la consulta
        query_body = {
            "query": {
                "bool": {
                    "filter": []
                }
            },
            "size": 100,
            "sort": [{"@timestamp": {"order": "desc"}}]
        }

        # Si se proporciona un parámetro 'before', filtrar logs anteriores a ese timestamp
        if before:
            query_body["query"]["bool"]["filter"].append({
                "range": {
                    "@timestamp": {
                        "lt": before
                    }
                }
            })

        # Buscar logs en Elasticsearch
        response = await es.search(
            index=index_name,
            body=query_body
        )

        # Transformar los logs al formato esperado por el modelo Log
        logs = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            log_entry = Log(
                timestamp=source.get("@timestamp", ""),
                device_id=source.get("host", {}).get("id", None),
                user_id=source.get("winlog", {}).get("user", {}).get("identifier", None),
                action=source.get("event", {}).get("action", None) if source.get("event", {}).get("action") != "None" else source.get("event", {}).get("code", None),
                status=source.get("log", {}).get("level", None),
                source=source.get("event", {}).get("provider", source.get("host", {}).get("hostname", None)),
            )
            logs.append(log_entry)

        return logs

    except NotFoundError:
        return []
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Elasticsearch: {str(e)}")
    except RequestError as e:
        raise HTTPException(status_code=400, detail=f"Elasticsearch query error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching logs: {str(e)}")
    finally:
        await es.close()