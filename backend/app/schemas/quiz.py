from pydantic import BaseModel
from pydantic import ConfigDict


class QuizBase(BaseModel):
    """Base schema for Quiz."""
    type: str
    question: str
    answer: str
    options: str

class QuizCreate(QuizBase):
    """Schema for creating a quiz."""
    video_id: int

class QuizUpdate(BaseModel):
    """Schema for updating a quiz."""
    question: str | None = None
    answer: str | None = None
    options: str | None = None

class QuizRead(QuizBase):
    """Schema for reading quiz data."""
    id: int
    video_id: int
    model_config = ConfigDict(
        from_attributes=True,
    )