from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth, logs, register

app = FastAPI()

# Configurar CORS para permitir solicitudes desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000", "http://107.152.39.90:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(auth.router, prefix="/token")
app.include_router(logs.router, prefix="/logs")
app.include_router(register.router, prefix="/api")  # Añade el router de register

@app.get("/")
async def root():
    return {"message": "Welcome to Nubla SIEM API"}