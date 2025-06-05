from fastapi import APIRouter, BackgroundTasks
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health(background_tasks: BackgroundTasks):
    return {"status": "healthy"}