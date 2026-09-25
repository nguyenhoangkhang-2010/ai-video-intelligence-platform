from unittest.mock import MagicMock, patch

import pytest

from ai.retrieval.dense_retriever import DenseRetriever
from ai.retrieval.hybrid_search import HybridRetriever
from app.api.deps import _get_cross_encoder_reranker, get_rag_pipeline


@pytest.fixture(autouse=True)
def _clear_reranker_cache():
    """
    _get_cross_encoder_reranker is process-wide cached (@lru_cache) so
    a real model is loaded at most once - tests must reset that cache
    before and after each test so one test's patched behavior can't
    leak into another.
    """
    _get_cross_encoder_reranker.cache_clear()
    yield
    _get_cross_encoder_reranker.cache_clear()


def _patched_semantic_search_service():
    return patch("app.api.deps.SemanticSearchService", return_value=MagicMock())


def test_get_rag_pipeline_uses_hybrid_retriever_when_enabled():
    with (
        _patched_semantic_search_service(),
        patch("app.api.deps.settings.retrieval.hybrid_enabled", True),
        patch("app.api.deps.settings.retrieval.reranking_enabled", False),
    ):
        pipeline = get_rag_pipeline(db=MagicMock())

    retriever = pipeline.retrieval_pipeline.retriever
    assert isinstance(retriever, HybridRetriever)
    assert len(retriever.retrievers) == 2
    assert pipeline.retrieval_pipeline.reranker is None


def test_get_rag_pipeline_uses_dense_only_when_hybrid_disabled():
    with (
        _patched_semantic_search_service(),
        patch("app.api.deps.settings.retrieval.hybrid_enabled", False),
        patch("app.api.deps.settings.retrieval.reranking_enabled", False),
    ):
        pipeline = get_rag_pipeline(db=MagicMock())

    assert isinstance(pipeline.retrieval_pipeline.retriever, DenseRetriever)


def test_get_rag_pipeline_attaches_reranker_when_enabled_and_loadable():
    fake_reranker = MagicMock(name="cross_encoder_reranker")

    with (
        _patched_semantic_search_service(),
        patch("app.api.deps.settings.retrieval.hybrid_enabled", False),
        patch("app.api.deps.settings.retrieval.reranking_enabled", True),
        patch(
            "ai.reranking.cross_encoder.CrossEncoderReranker",
            return_value=fake_reranker,
        ),
    ):
        pipeline = get_rag_pipeline(db=MagicMock())

    assert pipeline.retrieval_pipeline.reranker is fake_reranker


def test_get_rag_pipeline_falls_back_gracefully_when_reranker_fails_to_load():
    """
    The core graceful-fallback requirement: a broken/unavailable
    reranker model must never break a RAG request - get_rag_pipeline
    must still return a working pipeline, just without a reranker.
    """
    with (
        _patched_semantic_search_service(),
        patch("app.api.deps.settings.retrieval.hybrid_enabled", False),
        patch("app.api.deps.settings.retrieval.reranking_enabled", True),
        patch(
            "ai.reranking.cross_encoder.CrossEncoderReranker",
            side_effect=OSError("model not found locally and network is unavailable"),
        ),
    ):
        pipeline = get_rag_pipeline(db=MagicMock())

    assert pipeline.retrieval_pipeline.reranker is None
    # A second call must not re-attempt the (still-failing) load - the
    # failure is cached too, not retried on every request.
    with _patched_semantic_search_service():
        pipeline_2 = get_rag_pipeline(db=MagicMock())
    assert pipeline_2.retrieval_pipeline.reranker is None


def test_get_rag_pipeline_skips_reranker_entirely_when_disabled():
    with (
        _patched_semantic_search_service(),
        patch("app.api.deps.settings.retrieval.hybrid_enabled", False),
        patch("app.api.deps.settings.retrieval.reranking_enabled", False),
        patch("ai.reranking.cross_encoder.CrossEncoderReranker") as mock_cls,
    ):
        pipeline = get_rag_pipeline(db=MagicMock())

    assert pipeline.retrieval_pipeline.reranker is None
    mock_cls.assert_not_called()
