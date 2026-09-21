from unittest.mock import MagicMock

from ai.retrieval.sparse_retriever import SparseRetriever


def _make_chunk(vector_id, video_id, chunk_index, chunk_text):
    chunk = MagicMock(name=f"chunk_{vector_id}")
    chunk.vector_id = vector_id
    chunk.video_id = video_id
    chunk.chunk_index = chunk_index
    chunk.chunk_text = chunk_text
    return chunk


def test_retrieve_scopes_to_the_requested_video():
    embedding_repository = MagicMock(name="embedding_repository")
    embedding_repository.get_by_video_id.return_value = []

    retriever = SparseRetriever(embedding_repository=embedding_repository)

    retriever.retrieve(query="budget", video_id=10, top_k=5)

    embedding_repository.get_by_video_id.assert_called_once_with(10)


def test_retrieve_returns_empty_for_blank_query_without_touching_repository():
    embedding_repository = MagicMock(name="embedding_repository")

    retriever = SparseRetriever(embedding_repository=embedding_repository)

    results = retriever.retrieve(query="   ", video_id=10, top_k=5)

    assert results == []
    embedding_repository.get_by_video_id.assert_not_called()


def test_retrieve_returns_empty_when_video_has_no_chunks():
    embedding_repository = MagicMock(name="embedding_repository")
    embedding_repository.get_by_video_id.return_value = []

    retriever = SparseRetriever(embedding_repository=embedding_repository)

    results = retriever.retrieve(query="budget", video_id=10, top_k=5)

    assert results == []


def test_retrieve_ranks_keyword_matching_chunk_above_unrelated_chunk():
    # A degenerate 2-document corpus makes BM25's IDF math unreliable
    # (a term in exactly half of 2 docs can legitimately score ~0) -
    # use a corpus sized closer to a real video's chunk count instead.
    best_match = _make_chunk(
        "v1", 10, 2,
        "Marketing presented a new budget forecast for the campaign.",
    )
    partial_match = _make_chunk(
        "v2", 10, 1,
        "The quarterly budget review covers spending and forecasts.",
    )
    unrelated_a = _make_chunk(
        "v3", 10, 0,
        "The weather today is sunny with a light breeze.",
    )
    unrelated_b = _make_chunk(
        "v4", 10, 3,
        "The office picnic is scheduled for next Friday afternoon.",
    )

    embedding_repository = MagicMock(name="embedding_repository")
    embedding_repository.get_by_video_id.return_value = [
        unrelated_a, partial_match, best_match, unrelated_b,
    ]

    retriever = SparseRetriever(embedding_repository=embedding_repository)

    results = retriever.retrieve(query="budget forecast", video_id=10, top_k=5)

    result_ids = [r.id for r in results]
    assert result_ids[0] == "v1"
    assert "v3" not in result_ids
    assert "v4" not in result_ids

    assert results[0].text == best_match.chunk_text
    assert results[0].video_id == 10
    assert results[0].metadata["chunk_index"] == 2
    assert results[0].metadata["source"] == "sparse"
    # BM25 score is already higher-is-better - no conversion applied.
    assert results[0].score > 0


def test_retrieve_respects_top_k():
    chunks = [
        _make_chunk(f"v{i}", 10, i, f"budget report section {i} details")
        for i in range(10)
    ]
    embedding_repository = MagicMock(name="embedding_repository")
    embedding_repository.get_by_video_id.return_value = chunks

    retriever = SparseRetriever(embedding_repository=embedding_repository)

    results = retriever.retrieve(query="budget report", video_id=10, top_k=3)

    assert len(results) <= 3
