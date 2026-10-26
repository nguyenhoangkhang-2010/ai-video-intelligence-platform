import logging

from ai.retrieval.retriever import RetrievalResult, Retriever
from app.config.settings import settings


logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Combines any number of Retriever implementations (typically dense
    + sparse) via Reciprocal Rank Fusion (RRF).

    RRF is used instead of a raw/normalized weighted score sum
    because different retrievers' scores live on incomparable scales
    (dense's converted FAISS distance vs. sparse's BM25 score) - RRF
    only needs each retriever's RANK ordering, not its raw score
    magnitude, so this class never needs to know how any given
    retriever computed its score, keeping it generic over whatever
    Retriever implementations it is given.

    fusion_k controls how much weight top-ranked results get (lower
    k = top ranks dominate more); it defaults from
    settings.retrieval.rrf_k (one configurable place, per project
    convention) but can be overridden per instance.
    """

    def __init__(
        self,
        retrievers: list[Retriever],
        fusion_k: int | None = None,
    ):
        if not retrievers:
            raise ValueError(
                "HybridRetriever requires at least one retriever."
            )

        self.retrievers = retrievers
        self.fusion_k = (
            fusion_k
            if fusion_k is not None
            else settings.retrieval.rrf_k
        )

    def retrieve(
        self,
        query: str,
        video_id: int,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if not query or not query.strip():
            return []

        fused_scores: dict[str, float] = {}
        result_by_id: dict[str, RetrievalResult] = {}

        for retriever in self.retrievers:
            ranked_results = retriever.retrieve(
                query=query,
                video_id=video_id,
                top_k=top_k,
            )

            for rank, result in enumerate(ranked_results, start=1):
                fused_scores[result.id] = (
                    fused_scores.get(result.id, 0.0)
                    + 1.0 / (self.fusion_k + rank)
                )

                # The first retriever to surface a given id "wins"
                # the canonical text/metadata. Ids are stable across
                # retrievers (both DenseRetriever and SparseRetriever
                # key on the same Embedding.vector_id), so the same
                # chunk found by multiple retrievers fuses into one
                # result instead of appearing twice.
                result_by_id.setdefault(result.id, result)

        ranked_ids = sorted(
            fused_scores,
            key=lambda result_id: fused_scores[result_id],
            reverse=True,
        )

        fused_results = []

        for result_id in ranked_ids[:top_k]:
            original = result_by_id[result_id]

            fused_results.append(
                RetrievalResult(
                    id=original.id,
                    video_id=original.video_id,
                    text=original.text,
                    score=fused_scores[result_id],
                    metadata={
                        **original.metadata,
                        "fusion": "rrf",
                    },
                )
            )

        logger.info(
            "Hybrid retrieval fused %s retriever(s) into %s "
            "result(s) for video %s.",
            len(self.retrievers),
            len(fused_results),
            video_id,
        )

        return fused_results
