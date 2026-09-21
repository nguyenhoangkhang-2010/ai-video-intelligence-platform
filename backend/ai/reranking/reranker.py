from typing import Protocol, runtime_checkable

from ai.retrieval.retriever import RetrievalResult


@runtime_checkable
class Reranker(Protocol):
    """
    Structural contract for anything that re-scores/re-orders a list
    of already-retrieved candidates for a query.

    Mirrors ai.retrieval.retriever.Retriever's Protocol-based design:
    no inheritance required, so CrossEncoderReranker or any future
    reranker implementation only needs to match this shape. Kept
    generic on purpose - nothing here mentions cross-encoders or any
    specific model, so a reranker could just as well be a simpler
    heuristic later without RetrievalPipeline (or anything above it)
    changing.
    """

    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """
        Return `candidates` re-scored and re-ordered by relevance to
        `query`, most relevant first (score is always higher-is-
        better, regardless of how the underlying retriever scored
        them). Implementations must not introduce results that
        weren't in `candidates`, and must not change any result's
        `id`/`video_id`/`text` - only `score` (and optionally
        `metadata`) may differ in the returned results.
        """
        ...
