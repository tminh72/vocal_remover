from pathlib import Path
import uuid

import shutil

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Duration, Limiter, Rate
from pydantic import BaseModel

from app.core.security import get_current_user
from app.db import get_conn
from app.services.audio_processing import SAMPLE_DIR
from app.worker.tasks import process_audio

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp3", ".wav"}
SOURCE_DIR = Path("data/source")

_limiter = Limiter(Rate(2, Duration.SECOND * 30))


def _rate_limit_callback(*_, **__) -> None:
    raise HTTPException(status_code=429, detail="Please wait for the next attempt")


class SeparateResponse(BaseModel):
    task_id: str


class SeparateRequest(BaseModel):
    filename: str

@router.post(
    "/separate",
    response_model=SeparateResponse,
    dependencies=[Depends(RateLimiter(limiter=_limiter, callback=_rate_limit_callback))],
)
def separate(
    payload: SeparateRequest,
    current_user: dict = Depends(get_current_user),
) -> SeparateResponse:
    ext = Path(payload.filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .mp3 or .wav")

    source_path = SAMPLE_DIR / payload.filename
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="File not found in sampledata")

    record_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    conn = get_conn()
    conn.execute(
        "INSERT INTO audio_tasks (id, user_id, task_id, status, log, original_file_path, vocal_path, music_path, duration) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            record_id,
            current_user["id"],
            task_id,
            "queued",
            "",
            str(source_path),
            None,
            None,
            0.0,
        ),
    )
    conn.commit()
    conn.close()

    process_audio.delay(record_id, str(source_path))

    return SeparateResponse(task_id=task_id)
