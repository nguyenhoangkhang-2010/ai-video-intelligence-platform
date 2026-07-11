from app.repositories.user import UserRepository


class AuthService:
    """Service for authentication and user management."""

    def __init__(
        self,
        user_repository: UserRepository,
    ) -> None:
        self.user_repository = user_repository