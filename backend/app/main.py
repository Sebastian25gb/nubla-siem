from fastapi import FastAPI
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Import absoluto dentro del paquete para evitar ModuleNotFoundError
from backend.app.core.logging import configure_logging

app = FastAPI(title="Nubla SIEM API")
configure_logging()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)