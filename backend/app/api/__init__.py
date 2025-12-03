from fastapi import APIRouter
from backend.app.api.routes.alias import router as alias_router
from backend.app.api.routes.ingest import router as ingest_router

api_router = APIRouter()
api_router.include_router(alias_router)
api_router.include_router(ingest_router)