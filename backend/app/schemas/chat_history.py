from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class ChatHistoryBase(BaseModel):
    """Base schema for ChatHistory."""
    question: str
    answer: str

class ChatHistoryCreate(ChatHistoryBase):
    """Schema for creating chat history."""
    user_id: int
    video_id: int

class ChatHistoryRead(ChatHistoryBase):
    """Schema for reading chat history."""
    id: int
    user_id: int
    video_id: int
    created_at: datetime
    model_config = ConfigDict(
        from_attributes=True,
    )