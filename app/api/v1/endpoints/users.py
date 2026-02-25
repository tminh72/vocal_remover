from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from app.core.security import get_current_user
from app.db import get_conn

router = APIRouter()


class MeResponse(BaseModel):
    email: EmailStr
    credits: int


@router.get("/me", response_model=MeResponse)
def me(current_user: dict = Depends(get_current_user)) -> MeResponse:
    
    return MeResponse(
        email=current_user["email"],
        credits=current_user["credits"],
    )
