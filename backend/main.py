# /root/nubla-siem/backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api.routes import auth, logs, register, users, mfa, normalizer

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000", "http://107.152.39.90:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth, prefix="/token")
app.include_router(logs, prefix="/logs")
app.include_router(register, prefix="/api")
app.include_router(users, prefix="/api")
app.include_router(mfa, prefix="/api")
app.include_router(normalizer, prefix="/normalizer")

@app.get("/")
async def root():
    return {"message": "Welcome to Nubla SIEM API"}