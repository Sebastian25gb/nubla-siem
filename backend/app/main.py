from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

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
