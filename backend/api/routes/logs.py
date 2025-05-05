from fastapi import APIRouter, Depends, HTTPException
from typing import List
from api.schemas.logs import Log
from services.elasticsearch import get_logs
from core.security import get_current_user

router = APIRouter()

@router.get("/", response_model=List[Log])
async def read_logs(tenant_id: str, current_user: str = Depends(get_current_user)):
    try:
        logs = get_logs(tenant_id)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))