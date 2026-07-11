from app.auth.jwt import create_access_token
from app.repositories.user import UserRepository
from app.core.exceptions import InvalidCredentialsError
from app.core.exceptions import UserAlreadyExistsError
from app.core.security import hash_password
from app.core.security import verify_password
from app.models.user import User
from app.schemas.user import UserCreate
from app.schemas.user import UserLogin


class AuthService:
    """Business logic for authentication."""
    def __init__(
        self,
        user_repository: UserRepository,
    ) -> None:
        self.user_repository = user_repository
        
    def register(
        self,
        user_data: UserCreate,
    ) -> User:
        """Register a new user."""
        if self.user_repository.exists_by_email(
            user_data.email,
        ):
            raise UserAlreadyExistsError(
                "Email already exists.",
            )

        if self.user_repository.exists_by_username(
            user_data.username,
        ):
            raise UserAlreadyExistsError(
                "Username already exists.",
            )
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hash_password(
                user_data.password,
            ),
        )

        return self.user_repository.create(
            user,
        )
        
    def login(
        self,
        login_data: UserLogin,
    ) -> str:
        """Authenticate user and return JWT."""

        raise NotImplementedError