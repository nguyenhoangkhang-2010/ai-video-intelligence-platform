from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=User,
        )

    def get_by_email(
        self,
        email: str,
    ) -> User | None:

        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

    def get_by_username(
        self,
        username: str,
    ) -> User | None:

        return (
            self.db.query(User)
            .filter(User.username == username)
            .first()
        )

    def exists_by_email(
        self,
        email: str,
    ) -> bool:

        return self.get_by_email(email) is not None

    def exists_by_username(
        self,
        username: str,
    ) -> bool:

        return self.get_by_username(username) is not None