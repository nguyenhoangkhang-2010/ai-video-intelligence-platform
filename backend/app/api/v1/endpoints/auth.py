from fastapi import APIRouter
from fastapi import Depends

from app.repositories.user import UserRepository

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.rate_limit import rate_limit
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
    dependencies=[Depends(rate_limit("register", settings.rate_limit.register_limit, 60))],
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
    dependencies=[Depends(rate_limit("login", settings.rate_limit.login_limit, 60))],
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