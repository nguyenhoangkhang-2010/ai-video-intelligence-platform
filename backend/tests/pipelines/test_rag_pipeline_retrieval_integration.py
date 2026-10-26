from unittest.mock import MagicMock

from app.pipelines.rag_pipeline import RAGPipeline


def _make_pipeline_with_reranker():
    semantic_search_service = MagicMock(name="semantic_search_service")
    embedding_service = MagicMock(name="embedding_service")
    answerer = MagicMock(name="answerer")
    reranker = MagicMock(name="reranker")

    pipeline = RAGPipeline(
        semantic_search_service=semantic_search_service,
        embedding_service=embedding_service,
        answerer=answerer,
        reranker=reranker,
    )

    return pipeline, semantic_search_service, embedding_service, answerer, reranker


def test_ask_with_reranker_builds_context_and_sources_from_reranked_order():
    pipeline, semantic_search_service, embedding_service, answerer, reranker = (
        _make_pipeline_with_reranker()
    )

    embedding_service.get_by_video_id.return_value = [MagicMock()]

    # Dense search returns "a" first, "b" second (nearest-first).
    semantic_search_service.search.return_value = [
        {
            "vector_id": "a", "video_id": 10, "chunk_index": 0,
            "chunk_text": "chunk A text", "distance": 0.1,
        },
        {
            "vector_id": "b", "video_id": 10, "chunk_index": 1,
            "chunk_text": "chunk B text", "distance": 0.2,
        },
    ]

    # Reranker flips the order: "b" is actually the more relevant one.
    reranker.rerank.side_effect = lambda query, candidates: list(
        reversed(candidates),
    )
    answerer.answer.return_value = "final answer"

    result = pipeline.ask(video_id=10, query="what happened?", top_k=5)

    assert result.status == "answered"
    assert result.answer == "final answer"
    assert reranker.rerank.called

    # sources reflect the RERANKED order (b before a), not the
    # original dense order - proving the integration actually uses
    # the reranker's output, not just building it and discarding it.
    assert [s.vector_id for s in result.sources] == ["b", "a"]

    # The context built for the LLM follows the reranked order too.
    context = answerer.answer.call_args.kwargs["context"]
    assert context.index("chunk B text") < context.index("chunk A text")


def test_ask_empty_query_never_reaches_retrieval_or_reranker_or_llm():
    pipeline, semantic_search_service, embedding_service, answerer, reranker = (
        _make_pipeline_with_reranker()
    )

    result = pipeline.ask(video_id=10, query="   ", top_k=5)

    assert result.status == "empty_query"
    assert not embedding_service.get_by_video_id.called
    assert not semantic_search_service.search.called
    assert not reranker.rerank.called
    assert not answerer.answer.called


def test_ask_no_embeddings_never_reaches_retrieval_or_reranker_or_llm():
    pipeline, semantic_search_service, embedding_service, answerer, reranker = (
        _make_pipeline_with_reranker()
    )

    embedding_service.get_by_video_id.return_value = []

    result = pipeline.ask(video_id=10, query="what happened?", top_k=5)

    assert result.status == "no_embeddings"
    assert not semantic_search_service.search.called
    assert not reranker.rerank.called
    assert not answerer.answer.called


def test_ask_no_relevant_chunks_never_calls_the_llm():
    pipeline, semantic_search_service, embedding_service, answerer, reranker = (
        _make_pipeline_with_reranker()
    )

    embedding_service.get_by_video_id.return_value = [MagicMock()]
    semantic_search_service.search.return_value = []
    reranker.rerank.return_value = []

    result = pipeline.ask(video_id=10, query="what happened?", top_k=5)

    assert result.status == "no_relevant_chunks"
    assert result.answer is None
    assert result.sources == []
    # The LLM must never be called when there is nothing to ground an
    # answer in - this is the important contract, regardless of
    # whether the (empty-candidate) reranker call itself happened.
    assert not answerer.answer.called
