"""
Health check endpoints.
"""
from fastapi import APIRouter
from app.config.settings import settings

router = APIRouter(
    tags=["Health"]
)

@router.get("/health")
async def health_check():
    """
    Basic application health check.
    """
    return {
        "status": "healthy",
        "service": settings.app.name,
        "version": settings.app.version,
    }