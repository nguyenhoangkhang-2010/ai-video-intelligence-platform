from typing import Literal

from pydantic import BaseModel

from app.schemas.search import SearchResult


RAGStatus = Literal[
    "answered",
    "empty_query",
    "no_embeddings",
    "no_relevant_chunks",
]


class RAGResult(BaseModel):
    """
    Internal RAG pipeline result contract.

    Not the Phase 3 API response contract — Phase 3 maps this to
    whatever HTTP response shape it needs.
    """

    video_id: int
    query: str
    status: RAGStatus
    answer: str | None = None
    sources: list[SearchResult]
