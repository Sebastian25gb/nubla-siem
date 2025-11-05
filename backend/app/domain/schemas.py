from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LogEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    host: Optional[str] = None
    facility: Optional[str] = None
    severity: Optional[str] = None
    message: str
    tenant_id: str = "default"