from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class TranslationBase(BaseModel):
    language: str
    subtitle: str

class TranslationCreate(TranslationBase):
    video_id: int

class TranslationUpdate(BaseModel):
    subtitle: str | None = None

class TranslationRead(TranslationBase):
    id: int
    video_id: int
    created_at: datetime
    model_config = ConfigDict(
        from_attributes=True,
    )