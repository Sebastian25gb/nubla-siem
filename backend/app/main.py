from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from backend.app.core.logging import configure_logging

# Routers existentes
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.tenants import router as tenants_router
from backend.app.api.routes.logs import router as logs_router
# Nuevos
from backend.app.api.routes.alias import router as alias_router
from backend.app.api.routes.stats import router as stats_router
from backend.app.api.routes.tenant_meta import router as tenant_meta_router

app = FastAPI(title="Nubla SIEM API")
configure_logging()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Orden lógico
app.include_router(auth_router)
app.include_router(tenants_router)
app.include_router(logs_router)
app.include_router(alias_router)
app.include_router(stats_router)
app.include_router(tenant_meta_router)