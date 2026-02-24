from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pydub import AudioSegment

from app.core.security import get_current_user
from app.db import get_conn

router = APIRouter()

SAMPLE_DIR = Path("data/sample")
SOURCE_DIR = Path("data/source")
VOCAL_DIR = Path("data/vocal")
MUSIC_DIR = Path("data/music")
ALLOWED_EXTENSIONS = {".mp3", ".wav"}


class SeparateResponse(BaseModel):
    task_id: str


class SeparateRequest(BaseModel):
    filename: str


@router.post("/separate", response_model=SeparateResponse)
def separate(
    payload: SeparateRequest,
    current_user: dict = Depends(get_current_user),
) -> SeparateResponse:
    ext = Path(payload.filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .mp3 or .wav")

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    VOCAL_DIR.mkdir(parents=True, exist_ok=True)
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)

    source_path = SAMPLE_DIR / payload.filename
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="File not found in sampledata")

    record_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    music_path = MUSIC_DIR / f"{task_id}.mp3"
    vocal_path = VOCAL_DIR / f"{task_id}.mp3"

    audio = AudioSegment.from_file(source_path)
    # audio.export(wav_path, format="wav")
    # AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3")

    print("Processing audio...")
    
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
            str(music_path),
            0.0,
        ),
    )
    conn.commit()
    conn.close()

    return SeparateResponse(task_id=task_id)
