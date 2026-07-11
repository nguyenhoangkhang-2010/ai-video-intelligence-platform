from pydantic import BaseModel
from pydantic import ConfigDict


class FlashcardBase(BaseModel):
    """Base schema for Flashcard."""
    question: str
    answer: str
    difficulty: str

class FlashcardCreate(FlashcardBase):
    """Schema for creating a flashcard."""
    video_id: int

class FlashcardUpdate(BaseModel):
    """Schema for updating a flashcard."""
    question: str | None = None
    answer: str | None = None
    difficulty: str | None = None

class FlashcardRead(FlashcardBase):
    """Schema for reading flashcard data."""
    id: int
    video_id: int
    model_config = ConfigDict(
        from_attributes=True,
    )