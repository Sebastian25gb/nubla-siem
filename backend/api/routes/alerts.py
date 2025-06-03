from fastapi import APIRouter
from twilio.rest import Client

router = APIRouter()

@router.post("/alert")
async def send_alert(message: str, recipient: str):
    client = Client("TWILIO_SID", "TWILIO_TOKEN")
    client.messages.create(
        body=message,
        from_="+1234567890",
        to=recipient
    )
    return {"status": "sent"}