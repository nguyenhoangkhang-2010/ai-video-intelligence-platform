from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class EmbeddingBase(BaseModel):
    chunk_index: int
    chunk_text: str
    embedding_model: str
    vector_id: str

class EmbeddingCreate(EmbeddingBase):
    video_id: int

class EmbeddingRead(EmbeddingBase):
    id: int
    video_id: int
    created_at: datetime
    model_config = ConfigDict(
        from_attributes=True,
    )