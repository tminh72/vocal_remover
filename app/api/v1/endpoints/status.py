from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_user
from app.db import get_conn

router = APIRouter()


class StatusResponse(BaseModel):
    task_id: str
    status: str


@router.get("/status/{task_id}", response_model=StatusResponse)
def get_status(task_id: str, current_user: dict = Depends(get_current_user)) -> StatusResponse:
    conn = get_conn()
    row = conn.execute(
        "SELECT task_id, status FROM audio_tasks WHERE task_id = ? AND user_id = ?",
        (task_id, current_user["id"]),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    return StatusResponse(task_id=row["task_id"], status=row["status"])
