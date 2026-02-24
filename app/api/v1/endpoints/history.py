from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.db import get_conn

router = APIRouter()


class HistoryItem(BaseModel):
    task_id: str
    status: str
    original_file_path: str | None = None
    vocal_path: str | None = None
    music_path: str | None = None


@router.get("/history", response_model=List[HistoryItem])
def history(current_user: dict = Depends(get_current_user)) -> List[HistoryItem]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT task_id, status, original_file_path, vocal_path, music_path FROM audio_tasks WHERE user_id = ? ORDER BY rowid DESC",
        (current_user["id"],),
    ).fetchall()
    conn.close()

    return [
        HistoryItem(
            task_id=row["task_id"],
            status=row["status"],
            original_file_path=row["original_file_path"],
            vocal_path=row["vocal_path"],
            music_path=row["music_path"],
        )
        for row in rows
    ]
