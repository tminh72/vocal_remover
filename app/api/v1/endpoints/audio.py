from pathlib import Path
import uuid

import shutil

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from pydub import AudioSegment

from app.core.security import get_current_user
from app.db import get_conn

from os import getcwd
from os.path import basename, exists, join, splitext

import numpy as np

from spleeter.audio.adapter import AudioAdapter
from spleeter.separator import Separator

router = APIRouter()

SAMPLE_DIR = Path("data/sample")
SOURCE_DIR = Path("data/source")
OUTPUT_DIR = Path("data/output")
ALLOWED_EXTENSIONS = {".mp3", ".wav"}


class SeparateResponse(BaseModel):
    task_id: str


class SeparateRequest(BaseModel):
    filename: str


def save(upload: UploadFile, dest_dir: Path = SOURCE_DIR) -> Path:
    if Path(upload.filename).suffix.lower() != ".mp3":
        raise HTTPException(status_code=400, detail="Only .mp3")

    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4()}.mp3"
    dest_path = dest_dir / safe_name

    with dest_path.open("wb") as f:
        shutil.copyfileobj(upload.file, f)

    return dest_path


def split_to_vocal_and_accompaniment(source_path: Path, output_dir: Path) -> tuple[Path, Path]:
    if source_path.suffix.lower() != ".mp3":
        raise HTTPException(status_code=400, detail="Only .mp3")

    if not source_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    output_dir.mkdir(parents=True, exist_ok=True)
    separator = Separator("spleeter:2stems", multiprocess=False)
    separator.separate_to_file(str(source_path), str(output_dir))

    name = source_path.stem
    vocal_path = output_dir / name / "vocals.wav"
    accompaniment_path = output_dir / name / "accompaniment.wav"

    if not vocal_path.exists() or not accompaniment_path.exists():
        raise HTTPException(status_code=500, detail="Failed to split audio")

    return vocal_path, accompaniment_path


@router.post("/separate", response_model=SeparateResponse)
def separate(
    payload: SeparateRequest,
    current_user: dict = Depends(get_current_user),
) -> SeparateResponse:
    ext = Path(payload.filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .mp3 or .wav")

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    source_path = SAMPLE_DIR / payload.filename
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="File not found in sampledata")

    record_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    print("Processing audio...")
    vocal_path, accompaniment_path = split_to_vocal_and_accompaniment(source_path, OUTPUT_DIR)

    conn = get_conn()
    conn.execute(
        "INSERT INTO audio_tasks (id, user_id, task_id, status, log, original_file_path, vocal_path, music_path, duration) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            record_id,
            current_user["id"],
            task_id,
            "pending",
            "",
            str(source_path),
            str(vocal_path),
            str(accompaniment_path),
            0.0,
        ),
    )
    conn.commit()
    conn.close()

    return SeparateResponse(task_id=task_id)
