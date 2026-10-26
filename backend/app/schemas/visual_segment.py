from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict


class VisualSegmentBase(BaseModel):
    start_time: float
    end_time: float
    on_screen_text: str = ""
    description: str = ""


class VisualSegmentCreate(VisualSegmentBase):
    video_id: int
    frame_key: str | None = None


class VisualSegmentRead(VisualSegmentBase):
    id: int
    video_id: int
    speech_similarity: float | None = None
    # Derived, not stored: how this segment relates to the speech -
    # see ai.vision.segments.relation.
    relation: Literal["illustrates", "unrelated", "no-speech"] = "no-speech"
    # Present when a keyframe image was saved; the frame itself is
    # served by GET /videos/{video_id}/visual-segments/{id}/frame.
    has_frame: bool = False

    model_config = ConfigDict(
        from_attributes=True,
    )
