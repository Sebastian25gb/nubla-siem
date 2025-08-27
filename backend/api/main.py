from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import logs

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajusta a tus orígenes reales en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs, prefix="/logs")

@app.get("/")
async def root():
    return {"message": "Welcome to Nubla SIEM API"}
