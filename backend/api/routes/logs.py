from fastapi import APIRouter, Depends, HTTPException
from elasticsearch import AsyncElasticsearch, RequestError, ConnectionError
from elasticsearch.exceptions import NotFoundError
from .auth import get_current_user
from models.logs import Log
from datetime import datetime

router = APIRouter()

# Cliente de Elasticsearch
es = AsyncElasticsearch(
    hosts=["http://elasticsearch:9200"],
    basic_auth=("elastic", "yourpassword"),
    timeout=30,
    retry_on_timeout=True
)

# Modelo Log ajustado para incluir nuevos campos
class Log:
    def __init__(self, timestamp, device, user_id, action, status, network, source):
        self.timestamp = timestamp
        self.device = device
        self.user_id = user_id
        self.action = action
        self.status = status
        self.network = network
        self.source = source

@router.get("/")
async def fetch_logs(before: str = None, current_user: dict = Depends(get_current_user)):
    tenant_id = current_user.get("tenant")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID not found in token")

    # Usamos un índice fijo para testuser
    index_name = "nubla-logs-testuser"

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
                    "filter": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": "2025-05-17T00:00:00.000-05:00",
                                    "lte": "now"
                                }
                            }
                        }
                    ]
                }
            },
            "size": 100,
            "sort": [{"@timestamp": {"order": "desc"}}]
        }

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

        # Transformar los logs al formato deseado
        logs = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            # Formatear el timestamp
            timestamp_str = source.get("@timestamp", "")
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                formatted_timestamp = timestamp.strftime("%d/%m/%y %H:%M:%S")
            except ValueError:
                formatted_timestamp = timestamp_str

            # Determinar la acción (conexión/desconexión)
            event_code = source.get("event", {}).get("code", "")
            message = source.get("message", "")
            if event_code == "11005" and "seguridad inalámbrica" in message:
                action = "Wi-Fi Connected"
            elif event_code == "11004" and "seguridad inalámbrica" in message:
                action = "Wi-Fi Disconnected"
            else:
                action = source.get("event", {}).get("action", event_code)

            # Mapear el estado
            status = source.get("log", {}).get("level", "")
            if status == "información":
                status = "Success"
            elif "error" in status.lower():
                status = "Error"
            elif "warning" in status.lower():
                status = "Warning"

            log_entry = {
                "timestamp": formatted_timestamp,
                "device": source.get("winlog", {}).get("event_data", {}).get("Adapter", source.get("host", {}).get("name", "")),
                "user_id": source.get("winlog", {}).get("user", {}).get("identifier", ""),
                "action": action,
                "status": status,
                "network": source.get("winlog", {}).get("event_data", {}).get("SSID", ""),
                "source": source.get("event", {}).get("provider", source.get("host", {}).get("hostname", ""))
            }
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