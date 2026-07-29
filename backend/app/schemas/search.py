from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


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