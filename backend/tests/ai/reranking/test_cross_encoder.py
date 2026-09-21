from unittest.mock import MagicMock

from ai.reranking.cross_encoder import CrossEncoderReranker
from ai.retrieval.retriever import RetrievalResult


def _make_reranker_with_mock_model(predict_return_value):
    """
    CrossEncoderReranker.__init__ lazily imports and loads a real
    sentence-transformers CrossEncoder model - too heavy (and, in
    this project's current dev environment, actually broken due to
    an unrelated torchcodec/FFmpeg loading issue) for a unit test.
    Bypass __init__ entirely (mirroring the same technique already
    used for Embedder in this codebase's own tests) and inject a
    mock `.model` directly, so rerank()'s own logic - pair
    construction, sorting, score mapping - is exercised for real
    without ever importing sentence_transformers.
    """
    reranker = object.__new__(CrossEncoderReranker)
    reranker.model_name = "mock-model"
    reranker.model = MagicMock(name="cross_encoder_model")
    reranker.model.predict.return_value = predict_return_value
    return reranker


def _candidate(id, text, score=0.1, video_id=10):
    return RetrievalResult(id=id, video_id=video_id, text=text, score=score)


def test_rerank_returns_empty_for_empty_candidates_without_invoking_model():
    reranker = _make_reranker_with_mock_model(predict_return_value=[])

    results = reranker.rerank(query="q", candidates=[])

    assert results == []
    reranker.model.predict.assert_not_called()


def test_rerank_constructs_query_candidate_pairs_for_the_model():
    candidates = [
        _candidate("a", "first chunk text"),
        _candidate("b", "second chunk text"),
    ]
    reranker = _make_reranker_with_mock_model(predict_return_value=[0.1, 0.2])

    reranker.rerank(query="what happened?", candidates=candidates)

    pairs_passed = reranker.model.predict.call_args.args[0]
    assert pairs_passed == [
        ("what happened?", "first chunk text"),
        ("what happened?", "second chunk text"),
    ]


def test_rerank_sorts_candidates_by_model_score_descending():
    candidates = [
        _candidate("low", "irrelevant text"),
        _candidate("high", "highly relevant text"),
        _candidate("mid", "somewhat relevant text"),
    ]
    # Cross-encoder scores are higher-is-better - "high" gets the
    # largest score here.
    reranker = _make_reranker_with_mock_model(
        predict_return_value=[0.1, 0.9, 0.5],
    )

    results = reranker.rerank(query="q", candidates=candidates)

    assert [r.id for r in results] == ["high", "mid", "low"]
    assert [r.score for r in results] == [0.9, 0.5, 0.1]


def test_rerank_preserves_identity_and_metadata_only_replaces_score():
    candidate = _candidate("a", "text", score=0.42)
    reranker = _make_reranker_with_mock_model(predict_return_value=[0.99])

    results = reranker.rerank(query="q", candidates=[candidate])

    result = results[0]
    assert result.id == candidate.id
    assert result.video_id == candidate.video_id
    assert result.text == candidate.text
    assert result.score == 0.99
    assert result.metadata["rerank_score"] == 0.99
    assert result.metadata["original_score"] == 0.42
