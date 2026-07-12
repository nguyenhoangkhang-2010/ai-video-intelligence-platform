from fastapi import APIRouter
from fastapi import Depends

from app.database.session import get_db
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.repositories.video import VideoRepository
from app.services.video import VideoService

router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
)

@router.get("")
def get_my_videos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
): 
    """
    Get all videos of current user.
    """
    repository = VideoRepository(db)
    service = VideoService(repository)

    return service.get_user_videos(
        user_id=current_user.id,
    )