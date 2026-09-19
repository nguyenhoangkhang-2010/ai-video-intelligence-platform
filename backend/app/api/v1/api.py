from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.videos import router as videos_router
from app.api.v1.endpoints.processing_jobs import router as processing_jobs_router
from app.api.v1.endpoints.transcripts import router as transcripts_router
from app.api.v1.endpoints.search import router as search_router
from app.api.v1.endpoints.quizzes import router as quizzes_router
from app.api.v1.endpoints.summaries import router as summaries_router
from app.api.v1.endpoints.translations import router as translations_router


api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(videos_router)
api_router.include_router(processing_jobs_router)
api_router.include_router(transcripts_router)
api_router.include_router(search_router)
api_router.include_router(quizzes_router)
api_router.include_router(summaries_router)
api_router.include_router(translations_router)