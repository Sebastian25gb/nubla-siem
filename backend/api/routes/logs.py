from fastapi import APIRouter, Depends, HTTPException
from elasticsearch import AsyncElasticsearch, RequestError, ConnectionError
from elasticsearch.exceptions import NotFoundError
from .auth import get_current_user
from datetime import datetime

router = APIRouter()

es = AsyncElasticsearch(
    hosts=["http://elasticsearch:9200"],
    basic_auth=("elastic", "yourpassword"),
    timeout=30,
    retry_on_timeout=True
)

@router.get("/")
async def fetch_logs(before: str = None, current_user: dict = Depends(get_current_user)):
    tenant_id = current_user.get("tenant")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID not found in token")

    index_name = ".ds-nubla-logs-testuser-*"

    try:
        if not await es.ping():
            raise HTTPException(status_code=503, detail="Elasticsearch is not available")

        if not await es.indices.exists(index=index_name):
            return []

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

        response = await es.search(
            index=index_name,
            body=query_body
        )

        logs = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            # Usar winlog.event_data.TimeCreated o event.created como timestamp
            timestamp_str = source.get("winlog", {}).get("event_data", {}).get("TimeCreated", source.get("event", {}).get("created", source.get("@timestamp", "")))
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                formatted_timestamp = timestamp.strftime("%d/%m/%y %H:%M:%S")
            except ValueError:
                formatted_timestamp = timestamp_str

            event_code = source.get("event", {}).get("code", "")
            message = source.get("message", "")
            if event_code == "11005" and "seguridad inalámbrica" in message:
                action = "Wi-Fi Connected"
            elif event_code == "11004" and "seguridad inalámbrica" in message:
                action = "Wi-Fi Disconnected"
            else:
                action = source.get("event", {}).get("action", event_code)

            status = source.get("log", {}).get("level", "")
            if status == "información":
                status = "Success"
            elif "error" in status.lower():
                status = "Error"
            elif "warning" in status.lower():
                status = "Warning"

            # Usar host.ip en lugar de source.ip, tomando la primera IP de la lista
            ip = source.get("host", {}).get("ip", ["-"])[0]

            log_entry = {
                "timestamp": formatted_timestamp,
                "device": source.get("winlog", {}).get("event_data", {}).get("Adapter", source.get("host", {}).get("name", "")),
                "user_id": source.get("winlog", {}).get("user", {}).get("identifier", ""),
                "ip": ip,
                "action": action,
                "status": status,
                "network": source.get("winlog", {}).get("event_data", {}).get("SSID", ""),
                "source": source.get("event", {}).get("provider", source.get("host", {}).get("hostname", "")),
                "message": source.get("message", "")
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