import os
from pathlib import Path

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.db import init_db
from app.services.audio_processing import warmup_model

app = FastAPI(title="Vocal Remover POC")
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    if os.getenv("WARMUP_ON_START", "true").lower() == "true":
        sample_path = os.getenv("WARMUP_SAMPLE", "data/sample/warmup.mp3")
        warmup_model(Path(sample_path))
