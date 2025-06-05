# /root/nubla-siem/backend/api/routes/alerts.py
from fastapi import APIRouter
from twilio.rest import Client
from core.config import settings

router = APIRouter()

@router.post("/alert")
async def send_alert(message: str, recipient: str):
    client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
    client.messages.create(
        body=message,
        from_="+1234567890",
        to=recipient
    )
    return {"status": "sent"}