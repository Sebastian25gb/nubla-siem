from typing import Optional
from pydantic import BaseModel

class Log(BaseModel):
    timestamp: str
    device_id: Optional[str] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None