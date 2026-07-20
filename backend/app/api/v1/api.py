from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.videos import router as videos_router
from app.api.v1.endpoints.processing_jobs import router as processing_jobs_router
from app.api.v1.endpoints.transcripts import router as transcripts_router


api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(videos_router)
api_router.include_router(processing_jobs_router)
api_router.include_router(transcripts_router)