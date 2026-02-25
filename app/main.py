from fastapi import FastAPI

from app.api.v1.router import api_router
from app.db import init_db

app = FastAPI(title="Vocal Remover POC")
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
