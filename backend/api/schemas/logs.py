from pydantic import BaseModel
from datetime import datetime

class Log(BaseModel):
    timestamp: datetime
    tenant_id: str
    device_id: str
    user_id: str
    action: str
    status: str
    source: str

    class Config:
        from_attributes = True