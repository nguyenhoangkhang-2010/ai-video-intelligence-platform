import logging

from ai.retrieval.retriever import RetrievalResult
from app.services.semantic_search import SemanticSearchService


logger = logging.getLogger(__name__)


class DenseRetriever:
    """
    Retriever implementation backed by the existing dense/FAISS
    semantic search stack.

    No embedding generation, FAISS access, locking, or vector
    persistence is reimplemented here - this is purely an adapter
    that maps SemanticSearchService's existing dict-based result
    shape onto the generic RetrievalResult contract, and reuses
    SemanticSearchService.search() exactly as-is (same video_id
    scoping, same top_k semantics, same FAISS global-index-then-
    filter behavior).
    """

    def __init__(
        self,
        semantic_search_service: SemanticSearchService,
    ):
        self.semantic_search_service = semantic_search_service

    def retrieve(
        self,
        query: str,
        video_id: int,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        results = self.semantic_search_service.search(
            video_id=video_id,
            query=query,
            top_k=top_k,
        )

        return [
            self._to_retrieval_result(result)
            for result in results
        ]

    @staticmethod
    def _to_retrieval_result(result: dict) -> RetrievalResult:
        """
        SemanticSearchService returns a FAISS L2 `distance`, where a
        SMALLER value means a closer/better match - the opposite
        direction of RetrievalResult's retriever-defined `score`
        contract, which this project treats as higher-is-better so
        results from different retriever types can eventually be
        compared/fused without the caller needing to know each
        retriever's internal metric. This is the one place that
        conversion happens (1 / (1 + distance)); the raw distance is
        preserved in metadata for anything that needs it (e.g.
        reconstructing the existing SearchResult API contract).
        SemanticSearchService itself is untouched and keeps returning
        raw distance as before.
        """
        distance = result["distance"]
        score = 1.0 / (1.0 + distance)

        return RetrievalResult(
            id=result["vector_id"],
            video_id=result["video_id"],
            text=result["chunk_text"],
            score=score,
            metadata={
                "chunk_index": result["chunk_index"],
                "distance": distance,
                "source": "dense",
            },
        )
