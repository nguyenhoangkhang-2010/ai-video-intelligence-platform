from unittest.mock import MagicMock

from ai.retrieval.dense_retriever import DenseRetriever


def test_retrieve_delegates_to_semantic_search_service_with_correct_args():
    semantic_search_service = MagicMock(name="semantic_search_service")
    semantic_search_service.search.return_value = []

    retriever = DenseRetriever(
        semantic_search_service=semantic_search_service,
    )

    retriever.retrieve(query="what happened?", video_id=10, top_k=3)

    semantic_search_service.search.assert_called_once_with(
        video_id=10,
        query="what happened?",
        top_k=3,
    )


def test_retrieve_maps_search_results_onto_retrieval_result_contract():
    semantic_search_service = MagicMock(name="semantic_search_service")
    semantic_search_service.search.return_value = [
        {
            "vector_id": "v1",
            "video_id": 10,
            "chunk_index": 2,
            "chunk_text": "chunk one text",
            "distance": 0.25,
        },
    ]

    retriever = DenseRetriever(
        semantic_search_service=semantic_search_service,
    )

    results = retriever.retrieve(query="q", video_id=10, top_k=5)

    assert len(results) == 1
    result = results[0]
    assert result.id == "v1"
    assert result.video_id == 10
    assert result.text == "chunk one text"
    # FAISS distance is lower-is-better; RetrievalResult.score is
    # higher-is-better - assert the actual conversion, not just "some
    # score exists".
    assert result.score == 1.0 / (1.0 + 0.25)
    assert result.metadata["chunk_index"] == 2
    assert result.metadata["distance"] == 0.25
    assert result.metadata["source"] == "dense"


def test_retrieve_returns_empty_list_when_semantic_search_returns_nothing():
    semantic_search_service = MagicMock(name="semantic_search_service")
    semantic_search_service.search.return_value = []

    retriever = DenseRetriever(
        semantic_search_service=semantic_search_service,
    )

    results = retriever.retrieve(query="q", video_id=10, top_k=5)

    assert results == []


def test_lower_distance_produces_higher_score_ordering_is_preserved():
    semantic_search_service = MagicMock(name="semantic_search_service")
    # SemanticSearchService already returns results nearest-first
    # (ascending distance); confirm the score conversion keeps that
    # relative ordering (closer match -> higher score).
    semantic_search_service.search.return_value = [
        {"vector_id": "near", "video_id": 10, "chunk_index": 0, "chunk_text": "a", "distance": 0.1},
        {"vector_id": "far", "video_id": 10, "chunk_index": 1, "chunk_text": "b", "distance": 0.9},
    ]

    retriever = DenseRetriever(
        semantic_search_service=semantic_search_service,
    )

    results = retriever.retrieve(query="q", video_id=10, top_k=5)

    assert results[0].id == "near"
    assert results[1].id == "far"
    assert results[0].score > results[1].score
