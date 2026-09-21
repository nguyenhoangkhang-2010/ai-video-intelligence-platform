from unittest.mock import MagicMock, patch

from app.services.semantic_search import SemanticSearchService


def _make_service():
    """
    Build a SemanticSearchService with its two internally-constructed
    dependencies (Embedder, VectorStore) patched at their import site
    inside app.services.semantic_search, BEFORE the service is
    constructed, so __init__ never loads a real BGE-M3 model or a
    real FAISS index. embedding_repository is injected as a mock.
    """
    embedding_repository = MagicMock(name="embedding_repository")

    with (
        patch("app.services.semantic_search.Embedder") as mock_embedder_class,
        patch(
            "app.services.semantic_search.VectorStore",
        ) as mock_vector_store_class,
    ):
        service = SemanticSearchService(
            embedding_repository=embedding_repository,
        )

    return (
        service,
        embedding_repository,
        mock_embedder_class.return_value,
        mock_vector_store_class.return_value,
    )


def _make_embedding_record(video_id, chunk_index, chunk_text):
    record = MagicMock(name=f"embedding_record_{chunk_index}")
    record.video_id = video_id
    record.chunk_index = chunk_index
    record.chunk_text = chunk_text
    return record


def test_search_scopes_results_to_requested_video_and_excludes_other_videos():
    service, embedding_repository, embedder, vector_store = _make_service()

    # video 10 owns vector_ids "v1"/"v2"; the global FAISS index also
    # contains vectors belonging to a different video ("other-v1"/
    # "other-v2") at interleaved positions - exactly the scenario the
    # post-filter in SemanticSearchService.search() must handle.
    own_embeddings = [
        MagicMock(vector_id="v1"),
        MagicMock(vector_id="v2"),
    ]
    embedding_repository.get_by_video_id.return_value = own_embeddings

    vector_store.total_vectors.return_value = 4
    vector_store.index.search.return_value = (
        [[0.1, 0.2, 0.3, 0.4]],  # distances
        [[0, 1, 2, 3]],  # FAISS row positions
    )

    position_to_vector_id = {
        0: "v1",
        1: "other-v1",
        2: "v2",
        3: "other-v2",
    }
    vector_store.get_vector_id.side_effect = (
        lambda position: position_to_vector_id[position]
    )

    embedder.embed_query.return_value = [0.1, 0.2, 0.3, 0.4]

    embedding_records = {
        "v1": _make_embedding_record(10, 0, "chunk one text"),
        "v2": _make_embedding_record(10, 1, "chunk two text"),
    }
    embedding_repository.get_by_vector_id.side_effect = (
        lambda vector_id: embedding_records.get(vector_id)
    )

    results = service.search(video_id=10, query="what happened?", top_k=5)

    # Correct video_id passed into the repository layer that owns
    # video scoping.
    embedding_repository.get_by_video_id.assert_called_once_with(10)

    # Only this video's vector_ids are ever resolved against the DB -
    # the other video's vector_ids returned by FAISS are skipped
    # before get_by_vector_id is ever called on them.
    resolved_vector_ids = {
        call.args[0]
        for call in embedding_repository.get_by_vector_id.call_args_list
    }
    assert resolved_vector_ids == {"v1", "v2"}

    # Results are scoped to the requested video only.
    assert len(results) == 2
    assert all(result["video_id"] == 10 for result in results)
    assert {result["vector_id"] for result in results} == {"v1", "v2"}
    assert {result["chunk_text"] for result in results} == {
        "chunk one text", "chunk two text",
    }


def test_search_returns_empty_when_video_has_no_embeddings():
    service, embedding_repository, embedder, vector_store = _make_service()

    embedding_repository.get_by_video_id.return_value = []

    results = service.search(video_id=10, query="anything?", top_k=5)

    assert results == []

    embedding_repository.get_by_video_id.assert_called_once_with(10)

    # Existing short-circuit behavior preserved: no query embedding
    # or FAISS search is performed when the video owns no vectors.
    embedder.embed_query.assert_not_called()
    vector_store.index.search.assert_not_called()


def test_search_returns_empty_for_blank_query_without_touching_repository():
    service, embedding_repository, embedder, vector_store = _make_service()

    results = service.search(video_id=10, query="   ", top_k=5)

    assert results == []

    embedding_repository.get_by_video_id.assert_not_called()
    embedder.embed_query.assert_not_called()
    vector_store.index.search.assert_not_called()
