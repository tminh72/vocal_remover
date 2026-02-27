from pathlib import Path
import uuid

import shutil

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
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


def save(upload: UploadFile, dest_dir: Path = SOURCE_DIR) -> Path:
    if Path(upload.filename).suffix.lower() != ".mp3":
        raise HTTPException(status_code=400, detail="Only .mp3")

    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4()}.mp3"
    dest_path = dest_dir / safe_name

    with dest_path.open("wb") as f:
        shutil.copyfileobj(upload.file, f)

    return dest_path


@router.post(
    "/separate",
    response_model=SeparateResponse,
    dependencies=[Depends(RateLimiter(limiter=_limiter, callback=_rate_limit_callback))],
)
def separate(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
) -> SeparateResponse:
    source_path = save(file, SOURCE_DIR)

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


@router.get("/stream/{task_id}/{filename}")
def stream_audio(
    task_id: str,
    filename: str,
    current_user: dict = Depends(get_current_user),
):
    if filename not in {"vocals.wav", "accompaniment.wav"}:
        raise HTTPException(status_code=404, detail="File not found")

    conn = get_conn()
    row = conn.execute(
        "SELECT status, vocal_path, music_path FROM audio_tasks WHERE task_id = ? AND user_id = ?",
        (task_id, current_user["id"]),
    ).fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    if row["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")

    if filename == "accompaniment.wav":
        path = row["music_path"]
    else:
        path = row["vocal_path"]

    if not path:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type="audio/wav", filename=filename)
