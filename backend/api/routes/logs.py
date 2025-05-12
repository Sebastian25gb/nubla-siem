from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
from services.elasticsearch import get_logs
from core.security import get_current_user

router = APIRouter()

class Log(BaseModel):
    timestamp: str
    device_id: str
    user_id: str
    action: str
    status: str
    source: str
    tenant_id: str

@router.get("/", response_model=List[Log])
async def read_logs(current_user: dict = Depends(get_current_user)):
    try:
        # Usamos el nombre del tenant desde el token
        tenant_id = current_user["tenant"]
        logs = get_logs(tenant_id)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))