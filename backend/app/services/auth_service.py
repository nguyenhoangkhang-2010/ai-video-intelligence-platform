from app.repositories.user import UserRepository


class AuthService:
    """Authentication service."""

    def __init__(
        self,
        user_repository: UserRepository,
    ) -> None:
        self.user_repository = user_repository