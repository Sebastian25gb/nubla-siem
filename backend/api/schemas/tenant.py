from pydantic import BaseModel

class TenantBase(BaseModel):
    name: str

class Tenant(TenantBase):
    id: int

    class Config:
        from_attributes = True