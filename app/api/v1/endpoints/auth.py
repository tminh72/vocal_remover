from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.core.security import create_access_token, hash_password
from app.db import get_conn

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    conn = get_conn()
    row = conn.execute(
        "SELECT id, email, password_hash FROM users WHERE email = ?",
        (payload.email,),
    ).fetchone()
    conn.close()

    if not row or row["password_hash"] != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expire_at = datetime.now(timezone.utc) + timedelta(hours=1)
    token = create_access_token({"sub": row["email"], "exp": expire_at})
    return TokenResponse(access_token=token)
