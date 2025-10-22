from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.logs import router as logs_router  # Importa el 'router' y renómbralo para claridad

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajusta a tus orígenes reales en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs_router, prefix="/logs")  # Usa el router importado

@app.get("/")
async def root():
    return {"message": "Welcome to Nubla SIEM API"}