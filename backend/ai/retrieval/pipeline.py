import logging

from ai.reranking.reranker import Reranker
from ai.retrieval.retriever import RetrievalResult, Retriever
from app.config.settings import settings


logger = logging.getLogger(__name__)


class RetrievalPipeline:
    """
    Orchestrates a Retriever (dense, sparse, or hybrid - anything
    matching the Retriever protocol) and an optional Reranker into a
    final, deduplicated, top_k-limited list of RetrievalResults.

    Both collaborators are constructor-injected, so swapping dense
    for sparse/hybrid, or adding/removing reranking, is a one-line
    change at the call site - this class's own logic never changes.
    Retrieval and reranking stay strictly separate steps (never
    merged into one function's internals): retrieve -> dedupe ->
    [rerank] -> truncate. When a reranker is supplied, more
    candidates than `top_k` are fetched first (top_k *
    candidate_multiplier) so the reranker has real material to
    re-rank instead of just re-sorting an already-truncated list;
    with no reranker, exactly `top_k` candidates are fetched, which
    is the original (pre-reranking) behavior, unchanged.

    Not FastAPI/HTTP-aware, and does not call an LLM - purely a
    retrieval-layer concern, sitting below RAGPipeline.
    """

    def __init__(
        self,
        retriever: Retriever,
        reranker: Reranker | None = None,
        candidate_multiplier: int | None = None,
    ):
        self.retriever = retriever
        self.reranker = reranker
        self.candidate_multiplier = (
            candidate_multiplier
            if candidate_multiplier is not None
            else settings.retrieval.candidate_multiplier
        )

    def retrieve(
        self,
        query: str,
        video_id: int,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """
        Retrieve up to `top_k` chunks belonging to `video_id` for
        `query`. Never falls back to an unscoped/global search.
        """

        if not query or not query.strip():
            return []

        logger.info(
            "Retrieving for video %s.",
            video_id,
        )

        candidate_k = (
            top_k * self.candidate_multiplier
            if self.reranker is not None
            else top_k
        )

        results = self.retriever.retrieve(
            query=query,
            video_id=video_id,
            top_k=candidate_k,
        )

        deduplicated = self._deduplicate(results)

        if self.reranker is not None:
            deduplicated = self.reranker.rerank(
                query=query,
                candidates=deduplicated,
            )

        return deduplicated[:top_k]

    @staticmethod
    def _deduplicate(
        results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """
        Keep the first (highest-ranked) occurrence of each result id.

        A no-op with today's single retriever, which shouldn't return
        duplicates on its own - but this is exactly where merging
        overlapping results from multiple retrievers will need to
        happen once hybrid retrieval exists.
        """
        seen: set[str] = set()
        deduplicated = []

        for result in results:
            if result.id in seen:
                continue

            seen.add(result.id)
            deduplicated.append(result)

        return deduplicated
