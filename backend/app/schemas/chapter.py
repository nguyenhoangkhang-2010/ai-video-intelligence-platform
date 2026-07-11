from pydantic import BaseModel
from pydantic import ConfigDict


class ChapterBase(BaseModel):
    title: str
    start_time: int
    end_time: int
    summary: str

class ChapterCreate(ChapterBase):
    video_id: int

class ChapterUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None

class ChapterRead(ChapterBase):
    id: int
    video_id: int
    model_config = ConfigDict(
        from_attributes=True,
    )