from pydantic import BaseModel


class VideoMetadata(BaseModel):
    """
    Metadata extracted from a video file.
    """
    duration: int
    width: int
    height: int
    fps: float
    codec: str