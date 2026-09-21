import logging

from ai.retrieval.retriever import RetrievalResult
from app.config.settings import settings


logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Cross-encoder based Reranker implementation, using
    sentence-transformers (already a project dependency).

    Model lifecycle: the model is loaded once, in __init__, and
    reused for every rerank() call on this instance - callers own
    how long an instance lives (e.g. a single cached instance for a
    process), so the model is never reloaded per call. No separate
    model-serving process/cache layer is introduced here.

    sentence_transformers is imported lazily inside __init__ rather
    than at module level (unlike e.g. ai.embedding.embedder importing
    FlagEmbedding eagerly): in the environment this was developed in,
    importing sentence_transformers unconditionally pulls in
    torchcodec (a transitive dependency of its multimodal loader),
    which fails to load its native library there (an environment-
    specific FFmpeg/torchcodec version issue, unrelated to this
    project's own code). Deferring the import means this module - and
    anything that only needs the Reranker contract/type - stays
    importable and testable without the model needing to be
    loadable; the import only happens, and can only fail, when a
    CrossEncoderReranker is actually instantiated.
    """

    def __init__(
        self,
        model_name: str | None = None,
    ):
        from sentence_transformers import CrossEncoder

        self.model_name = (
            model_name
            or settings.retrieval.cross_encoder_model
        )

        logger.info(
            "Loading cross-encoder model: %s",
            self.model_name,
        )

        self.model = CrossEncoder(
            self.model_name,
        )

    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """
        Score each candidate against `query` with the cross-encoder
        and return them sorted most-relevant-first. Cross-encoder
        scores are higher-is-better, matching RetrievalResult's score
        contract directly - no conversion needed here (unlike
        DenseRetriever's FAISS distance).
        """

        if not candidates:
            return []

        pairs = [
            (query, candidate.text)
            for candidate in candidates
        ]

        logger.info(
            "Reranking %s candidate(s) with cross-encoder.",
            len(candidates),
        )

        scores = self.model.predict(pairs)

        reranked = sorted(
            zip(candidates, scores),
            key=lambda pair: pair[1],
            reverse=True,
        )

        return [
            RetrievalResult(
                id=candidate.id,
                video_id=candidate.video_id,
                text=candidate.text,
                score=float(score),
                metadata={
                    **candidate.metadata,
                    "rerank_score": float(score),
                    "original_score": candidate.score,
                },
            )
            for candidate, score in reranked
        ]
