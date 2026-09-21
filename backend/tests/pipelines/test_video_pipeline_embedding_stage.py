from unittest.mock import MagicMock, call, patch

import pytest

from app.pipelines.video_pipeline import VideoPipelineService
from app.schemas.embedding import EmbeddingCreate


def _make_pipeline():
    """
    Build a VideoPipelineService with its five internally-constructed
    AI workers patched at their import site inside
    app.pipelines.video_pipeline, BEFORE the service is constructed,
    so __init__ never loads a real Whisper/BGE-M3/Ollama model. All
    injected services are plain mocks. pipeline.embedding_worker ends
    up being the mocked EmbeddingWorker's instance (its
    `.return_value`), so its `.process()` can be configured directly.
    """
    video_service = MagicMock(name="video_service")
    transcript_service = MagicMock(name="transcript_service")
    summary_service = MagicMock(name="summary_service")
    embedding_service = MagicMock(name="embedding_service")
    translation_service = MagicMock(name="translation_service")
    processing_job_service = MagicMock(name="processing_job_service")
    quiz_service = MagicMock(name="quiz_service")

    with (
        patch("app.pipelines.video_pipeline.TranscriptionWorker"),
        patch("app.pipelines.video_pipeline.SummaryWorker"),
        patch("app.pipelines.video_pipeline.EmbeddingWorker"),
        patch("app.pipelines.video_pipeline.TranslationWorker"),
        patch("app.pipelines.video_pipeline.QuizWorker"),
    ):
        pipeline = VideoPipelineService(
            video_service=video_service,
            transcript_service=transcript_service,
            summary_service=summary_service,
            embedding_service=embedding_service,
            translation_service=translation_service,
            processing_job_service=processing_job_service,
            quiz_service=quiz_service,
        )

    return pipeline, embedding_service


def test_embedding_stage_raises_and_leaves_existing_embeddings_untouched_when_generation_is_empty():
    pipeline, embedding_service = _make_pipeline()

    transcript = MagicMock(name="transcript")
    transcript.text = "some transcript text"

    pipeline.embedding_worker.process.return_value = []

    with patch("app.pipelines.video_pipeline.VectorStore") as mock_vector_store_class:
        with pytest.raises(ValueError):
            pipeline.embedding_stage(
                job_id=1, video_id=10, transcript=transcript,
            )

    embedding_service.get_by_video_id.assert_not_called()
    embedding_service.delete_by_video_id.assert_not_called()
    mock_vector_store_class.assert_not_called()
    mock_vector_store_class.return_value.replace.assert_not_called()
    embedding_service.create_embedding.assert_not_called()


def test_embedding_stage_replaces_old_embeddings_on_success():
    pipeline, embedding_service = _make_pipeline()

    job_id = 1
    video_id = 10

    transcript = MagicMock(name="transcript")
    transcript.text = "hello world transcript"

    generated_embeddings = [
        {
            "vector": [0.1, 0.2, 0.3],
            "vector_id": "new-vec-1",
            "chunk_index": 0,
            "chunk_text": "chunk one text",
            "embedding_model": "BAAI/bge-m3",
        },
        {
            "vector": [0.4, 0.5, 0.6],
            "vector_id": "new-vec-2",
            "chunk_index": 1,
            "chunk_text": "chunk two text",
            "embedding_model": "BAAI/bge-m3",
        },
    ]
    pipeline.embedding_worker.process.return_value = generated_embeddings

    old_embedding_1 = MagicMock(name="old_embedding_1")
    old_embedding_1.vector_id = "old-vec-1"
    old_embedding_2 = MagicMock(name="old_embedding_2")
    old_embedding_2.vector_id = "old-vec-2"
    embedding_service.get_by_video_id.return_value = [
        old_embedding_1, old_embedding_2,
    ]

    with patch("app.pipelines.video_pipeline.VectorStore") as mock_vector_store_class:
        manager = MagicMock()
        manager.attach_mock(embedding_service.get_by_video_id, "get_by_video_id")
        manager.attach_mock(embedding_service.delete_by_video_id, "delete_by_video_id")
        manager.attach_mock(
            mock_vector_store_class.return_value.replace, "replace",
        )
        manager.attach_mock(embedding_service.create_embedding, "create_embedding")

        result = pipeline.embedding_stage(
            job_id=job_id, video_id=video_id, transcript=transcript,
        )

    # 1. embedding_worker received the transcript text and video_id.
    pipeline.embedding_worker.process.assert_called_once_with(
        transcript=transcript.text, video_id=video_id,
    )

    # 2. + 3. get_by_video_id / delete_by_video_id are called
    # positionally with video_id, matching the real implementation.
    embedding_service.get_by_video_id.assert_called_once_with(video_id)
    embedding_service.delete_by_video_id.assert_called_once_with(video_id)

    # 4. VectorStore is constructed with the expected dimension.
    mock_vector_store_class.assert_called_once_with(dimension=1024)

    # 5. replace() receives exactly the old vector_ids to remove and
    # the newly generated vectors/vector_ids, in generation order.
    mock_vector_store_class.return_value.replace.assert_called_once_with(
        remove_vector_ids={"old-vec-1", "old-vec-2"},
        vectors=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        vector_ids=["new-vec-1", "new-vec-2"],
    )

    # 6. + 7. create_embedding is called once per generated embedding,
    # each with an EmbeddingCreate carrying the exact expected fields.
    assert embedding_service.create_embedding.call_args_list == [
        call(EmbeddingCreate(
            video_id=video_id,
            chunk_index=0,
            chunk_text="chunk one text",
            embedding_model="BAAI/bge-m3",
            vector_id="new-vec-1",
        )),
        call(EmbeddingCreate(
            video_id=video_id,
            chunk_index=1,
            chunk_text="chunk two text",
            embedding_model="BAAI/bge-m3",
            vector_id="new-vec-2",
        )),
    ]

    # 8. embedding_stage returns exactly what the worker generated.
    assert result is generated_embeddings

    # Verify ordering: get_by_video_id -> delete_by_video_id ->
    # VectorStore.replace -> create_embedding calls.
    assert manager.mock_calls == [
        call.get_by_video_id(video_id),
        call.delete_by_video_id(video_id),
        call.replace(
            remove_vector_ids={"old-vec-1", "old-vec-2"},
            vectors=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            vector_ids=["new-vec-1", "new-vec-2"],
        ),
        call.create_embedding(EmbeddingCreate(
            video_id=video_id,
            chunk_index=0,
            chunk_text="chunk one text",
            embedding_model="BAAI/bge-m3",
            vector_id="new-vec-1",
        )),
        call.create_embedding(EmbeddingCreate(
            video_id=video_id,
            chunk_index=1,
            chunk_text="chunk two text",
            embedding_model="BAAI/bge-m3",
            vector_id="new-vec-2",
        )),
    ]
