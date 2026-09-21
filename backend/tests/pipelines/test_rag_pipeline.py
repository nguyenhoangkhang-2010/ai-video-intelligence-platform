from unittest.mock import MagicMock

from app.pipelines.rag_pipeline import RAGPipeline


def _make_pipeline():
    """
    RAGPipeline takes all three dependencies via constructor
    injection, so no patching is needed - a mock `answerer` is passed
    explicitly to guarantee no real RagAnswerer/OllamaClient is ever
    constructed.
    """
    semantic_search_service = MagicMock(name="semantic_search_service")
    embedding_service = MagicMock(name="embedding_service")
    answerer = MagicMock(name="answerer")

    pipeline = RAGPipeline(
        semantic_search_service=semantic_search_service,
        embedding_service=embedding_service,
        answerer=answerer,
    )

    return pipeline, semantic_search_service, embedding_service, answerer


def test_ask_empty_query_returns_empty_query_status_and_calls_nothing():
    pipeline, semantic_search_service, embedding_service, answerer = (
        _make_pipeline()
    )

    result = pipeline.ask(video_id=10, query="   ", top_k=5)

    assert result.status == "empty_query"
    assert result.video_id == 10
    assert result.query == "   "
    assert result.answer is None
    assert result.sources == []

    embedding_service.get_by_video_id.assert_not_called()
    semantic_search_service.search.assert_not_called()
    answerer.answer.assert_not_called()


def test_ask_no_embeddings_returns_no_embeddings_status_and_skips_search_and_llm():
    pipeline, semantic_search_service, embedding_service, answerer = (
        _make_pipeline()
    )

    embedding_service.get_by_video_id.return_value = []

    result = pipeline.ask(video_id=10, query="what happened?", top_k=3)

    assert result.status == "no_embeddings"
    assert result.video_id == 10
    assert result.query == "what happened?"
    assert result.answer is None
    assert result.sources == []

    embedding_service.get_by_video_id.assert_called_once_with(10)
    semantic_search_service.search.assert_not_called()
    answerer.answer.assert_not_called()


def test_ask_no_relevant_chunks_returns_that_status_and_skips_llm():
    pipeline, semantic_search_service, embedding_service, answerer = (
        _make_pipeline()
    )

    embedding_service.get_by_video_id.return_value = [MagicMock()]
    semantic_search_service.search.return_value = []

    result = pipeline.ask(video_id=10, query="what happened?", top_k=3)

    assert result.status == "no_relevant_chunks"
    assert result.video_id == 10
    assert result.query == "what happened?"
    assert result.answer is None
    assert result.sources == []

    semantic_search_service.search.assert_called_once_with(
        video_id=10,
        query="what happened?",
        top_k=3,
    )
    answerer.answer.assert_not_called()


def test_ask_successful_retrieval_returns_answered_status_with_sources():
    pipeline, semantic_search_service, embedding_service, answerer = (
        _make_pipeline()
    )

    embedding_service.get_by_video_id.return_value = [MagicMock()]

    search_results = [
        {
            "vector_id": "v1",
            "video_id": 10,
            "chunk_index": 0,
            "chunk_text": "chunk one text",
            "distance": 0.1,
        },
        {
            "vector_id": "v2",
            "video_id": 10,
            "chunk_index": 1,
            "chunk_text": "chunk two text",
            "distance": 0.2,
        },
    ]
    semantic_search_service.search.return_value = search_results
    answerer.answer.return_value = "This video is about X."

    result = pipeline.ask(
        video_id=10, query="what is this video about?", top_k=5,
    )

    assert result.status == "answered"
    assert result.video_id == 10
    assert result.query == "what is this video about?"
    assert result.answer == "This video is about X."

    assert len(result.sources) == 2
    assert result.sources[0].vector_id == "v1"
    assert result.sources[0].chunk_text == "chunk one text"
    assert result.sources[1].vector_id == "v2"
    assert result.sources[1].chunk_text == "chunk two text"

    # video_id / query / top_k forwarded correctly into retrieval.
    semantic_search_service.search.assert_called_once_with(
        video_id=10,
        query="what is this video about?",
        top_k=5,
    )

    # LLM is called exactly once, grounded in the retrieved chunks.
    answerer.answer.assert_called_once()
    call_kwargs = answerer.answer.call_args.kwargs
    assert call_kwargs["query"] == "what is this video about?"
    assert "chunk one text" in call_kwargs["context"]
    assert "chunk two text" in call_kwargs["context"]
