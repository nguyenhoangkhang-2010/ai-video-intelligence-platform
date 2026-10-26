from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class SummaryBase(BaseModel):
    type: str
    content: str
    model_name: str

class SummaryCreate(SummaryBase):
    video_id: int

class SummaryUpdate(BaseModel):
    content: str | None = None

class SummaryRead(SummaryBase):
    id: int
    video_id: int
    created_at: datetime
    model_config = ConfigDict(
        from_attributes=True,
    )