from unittest.mock import MagicMock, call, patch

from app.pipelines.video_pipeline import VideoPipelineService


def _make_pipeline():
    """
    Build a VideoPipelineService with its five internally-constructed
    AI workers patched at their import site inside
    app.pipelines.video_pipeline, BEFORE the service is constructed,
    so __init__ never loads a real Whisper/BGE-M3/Ollama model. All
    injected services are plain mocks.
    """
    video_service = MagicMock(name="video_service")
    transcript_service = MagicMock(name="transcript_service")
    summary_service = MagicMock(name="summary_service")
    embedding_service = MagicMock(name="embedding_service")
    translation_service = MagicMock(name="translation_service")
    processing_job_service = MagicMock(name="processing_job_service")
    quiz_service = MagicMock(name="quiz_service")
    chapter_service = MagicMock(name="chapter_service")

    with (
        patch("app.pipelines.video_pipeline.TranscriptionWorker"),
        patch("app.pipelines.video_pipeline.SummaryWorker"),
        patch("app.pipelines.video_pipeline.EmbeddingWorker"),
        patch("app.pipelines.video_pipeline.TranslationWorker"),
        patch("app.pipelines.video_pipeline.QuizWorker"),
        patch("app.pipelines.video_pipeline.ChapterTopicPipeline"),
    ):
        pipeline = VideoPipelineService(
            video_service=video_service,
            transcript_service=transcript_service,
            summary_service=summary_service,
            embedding_service=embedding_service,
            translation_service=translation_service,
            processing_job_service=processing_job_service,
            quiz_service=quiz_service,
            chapter_service=chapter_service,
        )

    return (
        pipeline,
        video_service,
        processing_job_service,
    )


def test_process_runs_stages_in_order_with_expected_arguments():
    pipeline, video_service, processing_job_service = _make_pipeline()

    job_id = 1
    video_id = 10
    file_path = "/tmp/video.mp4"

    transcript = MagicMock(name="transcript")
    transcript_segments = [{"start": 0.0, "end": 1.0, "text": "hello"}]

    # Focus on orchestration only: replace each stage (already public
    # methods on the service) with a mock, so this test never runs
    # real ffprobe/transcription/summary/embedding/translation/quiz/
    # chapter logic - that belongs to each stage's own tests.
    pipeline.metadata_stage = MagicMock(name="metadata_stage")
    pipeline.transcription_stage = MagicMock(
        name="transcription_stage",
        return_value=(transcript, transcript_segments),
    )
    pipeline.summary_stage = MagicMock(name="summary_stage")
    pipeline.embedding_stage = MagicMock(name="embedding_stage")
    pipeline.translation_stage = MagicMock(name="translation_stage")
    pipeline.quiz_stage = MagicMock(name="quiz_stage")
    pipeline.chapter_stage = MagicMock(name="chapter_stage")

    manager = MagicMock()
    manager.attach_mock(pipeline.metadata_stage, "metadata_stage")
    manager.attach_mock(pipeline.transcription_stage, "transcription_stage")
    manager.attach_mock(pipeline.summary_stage, "summary_stage")
    manager.attach_mock(pipeline.embedding_stage, "embedding_stage")
    manager.attach_mock(pipeline.translation_stage, "translation_stage")
    manager.attach_mock(pipeline.quiz_stage, "quiz_stage")
    manager.attach_mock(pipeline.chapter_stage, "chapter_stage")
    manager.attach_mock(video_service.update_status, "update_status")
    manager.attach_mock(
        processing_job_service.update_progress, "update_progress",
    )

    pipeline.process(job_id=job_id, video_id=video_id, file_path=file_path)

    # Correct job_id / video_id / file_path per stage.
    pipeline.metadata_stage.assert_called_once_with(
        job_id=job_id, video_id=video_id, file_path=file_path,
    )
    pipeline.transcription_stage.assert_called_once_with(
        job_id=job_id, video_id=video_id, file_path=file_path,
    )

    # The same transcript object (returned by transcription_stage) is
    # threaded into every downstream stage - assert_called_once_with
    # compares the mock's identity, so this proves it is the same
    # object, not merely an equal one.
    pipeline.summary_stage.assert_called_once_with(
        job_id=job_id, video_id=video_id, transcript=transcript,
    )
    pipeline.embedding_stage.assert_called_once_with(
        job_id=job_id, video_id=video_id, transcript=transcript,
    )
    pipeline.translation_stage.assert_called_once_with(
        job_id=job_id, video_id=video_id, transcript=transcript,
    )
    pipeline.quiz_stage.assert_called_once_with(
        job_id=job_id, video_id=video_id, transcript=transcript,
    )
    pipeline.chapter_stage.assert_called_once_with(
        job_id=job_id, video_id=video_id,
        transcript_segments=transcript_segments,
    )

    video_service.update_status.assert_called_once_with(
        video_id=video_id, status="processed",
    )
    processing_job_service.update_progress.assert_called_once_with(
        job_id=job_id, progress=100, current_step="Completed",
    )

    # Exact production order, not just "each was called".
    assert manager.mock_calls == [
        call.metadata_stage(
            job_id=job_id, video_id=video_id, file_path=file_path,
        ),
        call.transcription_stage(
            job_id=job_id, video_id=video_id, file_path=file_path,
        ),
        call.summary_stage(
            job_id=job_id, video_id=video_id, transcript=transcript,
        ),
        call.embedding_stage(
            job_id=job_id, video_id=video_id, transcript=transcript,
        ),
        call.translation_stage(
            job_id=job_id, video_id=video_id, transcript=transcript,
        ),
        call.quiz_stage(
            job_id=job_id, video_id=video_id, transcript=transcript,
        ),
        call.chapter_stage(
            job_id=job_id, video_id=video_id,
            transcript_segments=transcript_segments,
        ),
        call.update_status(video_id=video_id, status="processed"),
        call.update_progress(
            job_id=job_id, progress=100, current_step="Completed",
        ),
    ]
