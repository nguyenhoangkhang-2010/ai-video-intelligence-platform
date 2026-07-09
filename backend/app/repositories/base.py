from typing import Generic
from typing import Type
from typing import TypeVar

from sqlalchemy.orm import Session

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):

    def __init__(
        self,
        db: Session,
        model: Type[ModelType],
    ):
        self.db = db
        self.model = model

    def get_by_id(
        self,
        obj_id: int,
    ) -> ModelType | None:

        return (
            self.db.query(self.model)
            .filter(self.model.id == obj_id)
            .first()
        )

    def get_all(self) -> list[ModelType]:

        return self.db.query(self.model).all()

    def create(
        self,
        obj: ModelType,
    ) -> ModelType:

        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)

        return obj

    def delete(
        self,
        obj: ModelType,
    ) -> None:

        self.db.delete(obj)
        self.db.commit()