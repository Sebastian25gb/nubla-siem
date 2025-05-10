from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import logs, auth

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth, prefix="/token")
app.include_router(logs, prefix="/logs")

@app.get("/")
async def root():
    return {"message": "Welcome to Nubla SIEM API"}