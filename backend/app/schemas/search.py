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


class SemanticSearchResponse(BaseModel):
    video_id: int
    query: str
    results: list[SearchResult]