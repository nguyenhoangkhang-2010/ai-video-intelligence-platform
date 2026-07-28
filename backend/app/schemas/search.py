from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    indices: list[list[int]]
    distances: list[list[float]]


class SemanticSearchResponse(BaseModel):
    video_id: int
    query: str
    results: SearchResult