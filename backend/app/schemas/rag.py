from typing import Literal

from pydantic import BaseModel

from app.schemas.search import SearchResult


RAGStatus = Literal[
    "answered",
    "empty_query",
    "no_embeddings",
    "no_relevant_chunks",
    # Retrieval succeeded (there was real grounding context) but the
    # LLM call itself failed - connection refused, timed out, returned
    # a non-2xx status, an empty body, or a malformed body. Kept as
    # one status rather than exposing ai.llm.errors' specific subtypes
    # over the API: the frontend only needs "try again", the specific
    # cause is in the server logs (RAGPipeline.ask()).
    "generation_failed",
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
