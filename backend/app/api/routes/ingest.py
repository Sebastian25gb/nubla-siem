from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List
from backend.app.core.auth import get_current_user
from backend.app.core.opensearch_client import get_client
from backend.app.processing.utils import prepare_event

router = APIRouter()

@router.post("/logs/ingest")
def ingest_events(payload: Dict[str, Any], user=Depends(get_current_user)):
    es = get_client()
    events = payload.get("events")
    if events is None:
        events = [payload]
    indexed = 0
    errors: List[str] = []
    for evt in events:
        try:
            evt = prepare_event(evt)
            evt["tenant_id"] = "default"
            es.index(index="logs-default", body=evt)
            indexed += 1
        except Exception as e:
            errors.append(str(e))
    if errors:
        raise HTTPException(status_code=500, detail={"indexed": indexed, "errors": errors})
    return {"indexed": indexed}