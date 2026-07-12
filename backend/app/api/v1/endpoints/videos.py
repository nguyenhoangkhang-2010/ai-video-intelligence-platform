from fastapi import APIRouter
from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
)

@router.get("")
def get_my_videos(
    current_user: User = Depends(get_current_user),
): 
    """
    Get all videos of current user.
    """

    return {
        "message": "Video router is working",
        "user_id": current_user.id,
    }