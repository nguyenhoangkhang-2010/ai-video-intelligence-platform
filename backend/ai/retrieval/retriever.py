from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class RetrievalResult:
    """
    Retrieval-layer result contract.

    Deliberately more generic than app.schemas.search.SearchResult:
    that schema is shaped around the current FAISS/dense
    implementation specifically ("vector_id", "distance" as an
    L2 metric where lower is better). A retriever-agnostic contract
    needs a neutral "score" (a retriever decides its own direction/
    scale - a future sparse/BM25 retriever's score is
    higher-is-better, for instance) so a future hybrid retriever can
    combine results from multiple sources without the pipeline layer
    caring how each one computed its score.

    id          - chunk/document identity (e.g. an embedding's
                  vector_id for a dense retriever today).
    video_id    - the video this chunk belongs to; every retriever
                  implementation is video-scoped, never global.
    text        - the retrieved chunk's content.
    score       - retriever-defined relevance score.
    metadata    - anything else worth carrying through (e.g.
                  chunk_index, the source retriever's name, the raw
                  distance/score before any future normalization).
                  Kept as a plain dict rather than named fields so a
                  sparse/hybrid retriever isn't forced to invent
                  values for dense-specific concepts it doesn't have.
    """

    id: str
    video_id: int
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Retriever(Protocol):
    """
    Structural contract for anything that can retrieve chunks for a
    query, scoped to a single video.

    A Protocol (not an ABC) is used so existing and future retriever
    implementations don't need to inherit from anything - they only
    need to match this shape. This lets a DenseRetriever wrap the
    existing SemanticSearchService, a future SparseRetriever wrap a
    keyword index, and a future HybridRetriever compose both, all
    without RetrievalPipeline (or anything above it) changing.
    """

    def retrieve(
        self,
        query: str,
        video_id: int,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """
        Retrieve up to `top_k` chunks belonging to `video_id` that are
        relevant to `query`. Implementations must never return chunks
        from a different video_id.
        """
        ...
