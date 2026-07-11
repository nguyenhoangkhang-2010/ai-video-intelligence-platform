from fastapi import APIRouter
from fastapi import Depends

from app.repositories.user import UserRepository

from sqlalchemy.orm import Session

from app.database.session import get_db

from app.schemas.user import UserCreate
from app.schemas.user import UserRead
from app.schemas.user import UserLogin

from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post(
    "/register",
    response_model=UserRead,
    status_code=201,
)

def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """Register a new user."""

    user_repository = UserRepository(db)

    service = AuthService(
        user_repository=user_repository,
    )

    return service.register(user_data)

@router.post(
    "/login",
)

def login(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """Login user and return JWT token."""

    user_repository = UserRepository(db)

    service = AuthService(
        user_repository=user_repository,
    )

    access_token = service.login(
        login_data,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }