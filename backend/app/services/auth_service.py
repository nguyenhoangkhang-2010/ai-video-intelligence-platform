from app.repositories.user import UserRepository


class AuthService:
    """Business logic for authentication."""
    def __init__(
        self,
        user_repository: UserRepository,
    ) -> None:
        self.user_repository = user_repository