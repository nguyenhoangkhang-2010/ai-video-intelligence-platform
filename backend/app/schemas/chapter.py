from pydantic import BaseModel
from pydantic import ConfigDict


class ChapterBase(BaseModel):
    title: str
    # Matches the ORM model's actual column type (Float) - the
    # Chapter DB column has always been Float; this schema
    # previously declared `int`, which would reject any real,
    # sub-second ASR-derived timestamp (e.g. 12.5) with a validation
    # error. Fixed here since it directly blocks chapter persistence,
    # not a new design decision.
    start_time: float
    end_time: float
    # The ORM column is nullable=True (a chapter can legitimately
    # have only a title, no generated summary) - the schema
    # previously required a non-null string here too, mismatching
    # its own model for the same reason as start_time/end_time above.
    summary: str | None = None

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