from fastapi import APIRouter

from app.api.v1.endpoints.audio import router as audio_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.history import router as history_router
from app.api.v1.endpoints.status import router as status_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(audio_router, tags=["audio"])
api_router.include_router(status_router, tags=["audio"])
api_router.include_router(history_router, tags=["audio"])
