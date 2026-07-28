from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    index: int
    distance: float


class SemanticSearchResponse(BaseModel):
    video_id: int
    query: str
    results: list[SearchResult]