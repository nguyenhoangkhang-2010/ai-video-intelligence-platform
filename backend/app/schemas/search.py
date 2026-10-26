from pydantic import BaseModel
from pydantic import Field


class SearchRequest(BaseModel):
    query: str
    # Upper-bounded: an unbounded top_k both inflates rerank cost
    # (RetrievalPipeline over-fetches top_k * candidate_multiplier
    # candidates) and made RAGPipeline's context-truncation-vs-sources
    # mismatch bug easier to trigger in practice.
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    vector_id: str
    video_id: int
    chunk_index: int
    chunk_text: str
    distance: float
    # Where in the video this chunk was spoken (seconds), so a result
    # or citation can seek straight to it. None for videos processed
    # before chunk times were stored.
    start_time: float | None = None
    end_time: float | None = None
    # "speech" (said) or "visual" (shown on screen).
    source: str = "speech"


class SemanticSearchResponse(BaseModel):
    video_id: int
    query: str
    results: list[SearchResult]